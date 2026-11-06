"""Export OpenAPI from the actual application without starting services."""
from pathlib import Path
import sys
import json
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"backend"))
from app.main import app
(root/"docs"/"openapi.json").write_text(json.dumps(app.openapi(),indent=2,ensure_ascii=False)+"\n")
print("docs/openapi.json exported")
