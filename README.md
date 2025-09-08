# jsonmask

Masking y redacción de datos sensibles en dicts, JSON y logs — simple, configurable y listo para integrarse en pipelines y aplicaciones Python.

- pip: `pip install jsonmask`
- Soporta: Python 3.8+

---

## ¿Qué es jsonmask?

`jsonmask` es una pequeña librería para detectar y enmascarar información sensible dentro de estructuras de datos Python (dict/list), JSON y mensajes de logging. Está pensada para integrarse fácilmente en aplicaciones, scripts y pipelines CI/CD donde quieras prevenir que PII, tokens o cualquier dato confidencial se filtre a logs, dumps o salidas externas.

Principales objetivos:
- Enmascarado declarativo por reglas (paths, patrones, entropía).
- Integración plug-and-play con el sistema `logging` (handler y filter).
- Presets para PII comunes y capacidad de extender reglas por proyecto.
- Salida segura y configuraciones aptas para uso en CI.

---

## Características principales

- Enmascarado por path (dot notation, corchetes y comodines simples).
- Reglas por clave, por expresión regular o por heurística de entropía.
- Estrategias de enmascarado: `redact`, `partial`, `hash`, `replace`, `drop`.
- Handler/Filter para `logging` para interceptar y limpiar mensajes automáticamente.
- CLI básica para procesar archivos JSON/NDJSON.
- Exportable a JSON con reporte de cambios (opcional).

---

## Casos de uso

- Evitar que tokens/credenciales aparezcan en logs de producción.
- Preparar fixtures y dumps para compartir (anónimo).
- Preprocesar respuestas de APIs antes de almacenarlas en S3 o enviarlas a terceros.
- Escaneo rápido en CI para detectar valor sensible en salidas de tests.

---

## Instalación

```bash
pip install jsonmask
```

O para desarrollo (cuando el repo tenga extras):

```bash
git clone https://github.com/<tu-org>/jsonmask.git
cd jsonmask
pip install -e ".[dev]"
```

---

## Uso rápido — API

Enmascarar un diccionario con una regla simple:

```python
from jsonmask import mask, Masker

data = {
    "user": {"name": "Ana", "email": "ana@example.com"},
    "token": "eyJhbGciOiJIUzI1..."
}

rules = [
    {"path": "user.email", "strategy": "redact"},
    {"path": "token", "strategy": "hash"}
]

masked = mask(data, rules=rules)
print(masked)
# {
#   "user": {"name": "Ana", "email": "****"},
#   "token": "3a7bd3f..."  # hashed value
# }
```

Objeto `Masker` para reutilizar compilaciones de reglas (performante):

```python
from jsonmask import Masker

masker = Masker.from_rules(rules)
masked = masker.mask(data)
```

---

## Uso con logging

Agrega `MaskingHandler` o `MaskingFilter` para limpiar mensajes y estructuras pasadas al logger.

```python
import logging
from jsonmask import MaskingHandler, Masker

rules = [
    {"path": "request.headers.authorization", "strategy": "partial"},
    {"path": "user.email", "strategy": "redact"}
]

masker = Masker.from_rules(rules)

handler = logging.StreamHandler()
handler.addFilter(MaskingHandler(masker))  # también existe MaskingFilter si prefieres

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

logger.info("request", extra={"request": {"headers": {"authorization": "Bearer abc123"}}, "user": {"email": "a@b.c"}})
# El mensaje que sale por consola tendrá el authorization y email enmascarados.
```

---

## CLI

Procesar un archivo JSON o NDJSON:

```bash
# procesamiento sencillo
jsonmask mask --input data.json --rules rules.yml --output masked.json

# leer de stdin y escribir a stdout
cat data.ndjson | jsonmask mask --rules rules.yml > masked.ndjson
```

Opciones típicas:
- `--input` archivo JSON/NDJSON (si se omite, lee stdin).
- `--rules` archivo YAML/JSON con reglas.
- `--output` archivo de salida (si se omite, escribe stdout).
- `--report` generar reporte JSON con listados de campos enmascarados.

---

## Formato de reglas (YAML/JSON)

Ejemplo `rules.yml`:

```yaml
rules:
  - path: "user.email"
    strategy: "redact"        # redact, replace, hash, partial, drop
    replace_with: "****"

  - path: "cards.*.number"
    strategy: "partial"
    keep_start: 4
    keep_end: 4
    mask_char: "*"

  - path: "headers.authorization"
    strategy: "regex"
    pattern: "Bearer\\s+(.+)"
    replace_with: "Bearer ****"

  - path: "token"
    strategy: "entropy"
    entropy_min: 3.5
    replace_with: "***"
```

Soporte de paths:
- Notación punto: `user.email`
- Comodín por nivel: `cards.*.number`
- Índices: `items[0].id`
- (Opcional) JSONPath-lite en roadmap para queries más complejas.

---

## Estrategias de enmascarado

- redact: reemplaza con `****` (o `replace_with`).
- replace: usa `replace_with` literal.
- hash: aplica hashing (sha256) y muestra prefijo configurable.
- partial: conserva parte del valor (keep_start/keep_end) y rellena el resto con `mask_char`.
- regex: aplica regex con `pattern` y `replace_with` (soporta grupos).
- entropy: detecta valores de alta entropía y aplica `replace_with` (útil para tokens aleatorios).

---

## Presets y reglas PII

`jsonmask` incluye presets (opcional) para PII común:
- emails
- números de tarjeta (BIN + PAN heurístico)
- SSN / NIF (por país, si se configura)
- tokens JWT / bearer

Puedes cargar presets y combinarlos con reglas propias.

---

## Consideraciones de rendimiento

- `Masker` compila reglas para ejecución repetida (evitar recompilar en bucles).
- Recorrido iterativo (no recursivo profundo) para reducir riesgo de stack overflow.
- Para cargas de logs muy altas, recomendamos:
  - usar sampling (procesar sólo 1 de N mensajes),
  - pre-filtrado por keys relevantes,
  - ejecutar en hilo/proceso separado si es necesario.

---

## Buenas prácticas

- Prefiere reglas por `path` en lugar de solo regex para disminuir falsos positivos.
- Usa `Masker` reutilizable en servicios de larga vida para minimizar overhead.
- Mantén un archivo `rules.yml` versionado en el repo y revisado por seguridad.
- En CI, ejecuta `jsonmask` como paso antes de publicar artefactos que contengan datos.

---

## Roadmap (funciones planeadas)

- Aprendizaje automático para reducir falsos positivos (modo “learning”).
- Integración nativa con `structlog` y `Loguru`.
- Plugin pre-commit y GitHub Action para escaneo de commits/PRs.
- Exportadores para sistemas de ingestión (Fluentd/Logstash).
- JSONPath full support y presets por regiones (SSN por país).
- Extensiones en C para hotspots de rendimiento (opcional).

---

## Tests y CI

Incluye:
- pytest (casos unitarios de reglas, estrategia y handler).
- ejemplo de GitHub Action: run tests, build wheel, publicar versión.
- tests de integración con fixtures NDJSON.

---

## Contribuir

1. Fork del repo
2. Abrir branch `feature/xxx`
3. Añadir tests y documentación
4. Crear PR

Sigue el archivo `CONTRIBUTING.md` (cuando esté disponible) para más detalles.

---

## Licencia

MIT — ver `LICENSE` en el repo.

---

## Contacto / Mantenimiento

Mantenedor: raelcorrales (GitHub: https://github.com/raelcorrales)

Si quieres que genere la estructura inicial del repo (skeleton del paquete, tests básicos, CI y lista de issues para el MVP), lo creo ahora y te doy la lista de tareas que puedo subir como issues.