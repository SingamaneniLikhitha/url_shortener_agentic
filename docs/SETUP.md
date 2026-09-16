# Setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `/docs` for Swagger UI.

Run tests:
```bash
pytest -q
```

Run orchestrator demo:
```bash
python -m app.orchestrator
```
