#!/bin/bash
# Ejemplos de uso de la CLI de jsonmask

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "Ejemplos de CLI de jsonmask"
echo "======================================"

# Crear archivos temporales
TMP_DIR=$(mktemp -d)
DATA_FILE="$TMP_DIR/data.json"
RULES_FILE="$TMP_DIR/rules.yml"
OUTPUT_FILE="$TMP_DIR/output.json"
REPORT_FILE="$TMP_DIR/report.json"
NDJSON_FILE="$TMP_DIR/data.ndjson"

# Crear datos de ejemplo
cat > "$DATA_FILE" << 'EOF'
{
  "user": {
    "name": "Ana García",
    "email": "ana.garcia@example.com",
    "phone": "+34612345678"
  },
  "payment": {
    "card_number": "4111111111111111",
    "cvv": "123"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
}
EOF

# Crear reglas de ejemplo
cat > "$RULES_FILE" << 'EOF'
rules:
  - path: "user.email"
    strategy: "redact"
  - path: "user.phone"
    strategy: "partial"
    keep_start: 0
    keep_end: 4
  - path: "payment.card_number"
    strategy: "partial"
    keep_start: 4
    keep_end: 4
  - path: "payment.cvv"
    strategy: "redact"
  - path: "token"
    strategy: "hash"
    hash_prefix_length: 8
EOF

echo ""
echo "1. Enmascarar archivo JSON:"
echo "   jsonmask mask -i $DATA_FILE -r $RULES_FILE -o $OUTPUT_FILE"
jsonmask mask -i "$DATA_FILE" -r "$RULES_FILE" -o "$OUTPUT_FILE" -q
echo "   Resultado:"
cat "$OUTPUT_FILE"

echo ""
echo "======================================"
echo "2. Generar reporte de enmascarado:"
echo "   jsonmask mask -i $DATA_FILE -r $RULES_FILE --report $REPORT_FILE"
jsonmask mask -i "$DATA_FILE" -r "$RULES_FILE" --report "$REPORT_FILE" -q > /dev/null
echo "   Reporte:"
cat "$REPORT_FILE"

echo ""
echo "======================================"
echo "3. Validar archivo de reglas:"
echo "   jsonmask validate -r $RULES_FILE"
jsonmask validate -r "$RULES_FILE"

echo ""
echo "======================================"
echo "4. Listar estrategias disponibles:"
echo "   jsonmask list-strategies"
jsonmask list-strategies

echo ""
echo "======================================"
echo "5. Generar reglas de ejemplo:"
echo "   jsonmask generate-rules"
jsonmask generate-rules | head -20
echo "   ..."

echo ""
echo "======================================"
echo "6. Procesar NDJSON desde stdin:"

# Crear archivo NDJSON
cat > "$NDJSON_FILE" << 'EOF'
{"email": "user1@example.com", "name": "User 1"}
{"email": "user2@example.com", "name": "User 2"}
EOF

# Crear reglas simples para NDJSON
cat > "$TMP_DIR/simple_rules.yml" << 'EOF'
rules:
  - path: "email"
    strategy: "redact"
EOF

echo "   cat data.ndjson | jsonmask mask -r rules.yml --ndjson"
cat "$NDJSON_FILE" | jsonmask mask -r "$TMP_DIR/simple_rules.yml" --ndjson -q

# Limpiar
rm -rf "$TMP_DIR"

echo ""
echo "======================================"
echo "¡Ejemplos completados!"
echo "======================================"
