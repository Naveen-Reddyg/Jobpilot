#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
TMP_PDF="$(mktemp -t resume.XXXXXX.pdf)"
cat > "$TMP_PDF" <<'EOF'
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 18 Tf 50 80 Td (Test Resume) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000064 00000 n 
0000000123 00000 n 
0000000255 00000 n 
0000000415 00000 n 
trailer
<< /Root 1 0 R /Size 6 >>
startxref
486
%%EOF
EOF
curl -sS -i -X POST "$BASE_URL/api/v1/resume" \
  -F "file=@$TMP_PDF;type=application/pdf" \
  -H "Accept: application/json"
rm -f "$TMP_PDF"
