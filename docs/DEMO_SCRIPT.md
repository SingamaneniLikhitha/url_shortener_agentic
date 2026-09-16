
# Demo Script

## 1. Start the application

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
````

Open:

```text
http://127.0.0.1:8000/docs
```

## 2. Test URL Shortener

* Create a URL using `POST /api/urls`
* Resolve it using `GET /r/{code}`
* Check click count using `GET /api/urls/{code}/analytics`

## 3. Greenfield Scenario

Call:

```text
POST /api/orchestrate?scenario=greenfield
```

Show:

* Dependency graph
* Tests and Security running in parallel
* Validation gate
* Audit trail
* Metrics
* Human approval

Then approve the release using:

```text
POST /api/orchestrate/{run_id}/approve
```

## 4. Brownfield Scenario

Call:

```text
POST /api/orchestrate?scenario=brownfield
```

Show that the workflow considers:

* Existing system
* Backward compatibility
* Regression testing
* Incremental implementation

## 5. Ambiguous Scenario

Call:

```text
POST /api/orchestrate?scenario=ambiguous
```

Show that the workflow stops at the requirements stage and asks clarification questions instead of making assumptions.

## 6. Run Tests

```bash
.venv\Scripts\python.exe -m pytest -v
```

Expected:

```text
12 passed
```

