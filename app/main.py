from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime, timezone
import sqlite3
import secrets

from .orchestrator import AgenticOrchestrator




DB = "urls.db"

app = FastAPI(
    title="Agentic URL Shortener",
    version="1.0.0"
)


def get_db():
    """
    Create a short-lived SQLite connection.

    WAL mode allows readers and writers to operate with less contention,
    while timeout/busy_timeout allows SQLite to wait briefly for a lock.
    """
    conn = sqlite3.connect(
        DB,
        timeout=10,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=10000")

    return conn


def init_db():
    """Initialize database schema once during application startup."""
    conn = get_db()

    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                click_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clicks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT NOT NULL,
                clicked_at TEXT NOT NULL,
                user_agent TEXT,
                referrer TEXT
            )
            """
        )

        conn.commit()

    finally:
        conn.close()


class CreateURL(BaseModel):
    url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None


@app.on_event("startup")
def startup():
    init_db()


def code_for(url: str) -> str:
    return secrets.token_urlsafe(5).replace("-", "").replace("_", "")[:7]


@app.post("/api/urls", status_code=201)
def create_url(req: CreateURL):

    conn = get_db()

    try:
        code = req.custom_alias or code_for(str(req.url))

        if not code.replace("-", "").isalnum() or not 3 <= len(code) <= 32:
            raise HTTPException(
                400,
                "custom_alias must be 3-32 alphanumeric characters or hyphens"
            )

        conn.execute(
            """
            INSERT INTO urls(
                short_code,
                original_url,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                code,
                str(req.url),
                datetime.now(timezone.utc).isoformat(),
                req.expires_at.isoformat() if req.expires_at else None
            )
        )

        conn.commit()

        return {
            "short_code": code,
            "short_url": f"/r/{code}",
            "original_url": str(req.url)
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            409,
            "short code already exists"
        )

    finally:
        conn.close()


@app.get("/r/{code}")
def redirect_url(code: str):

    conn = get_db()

    try:
        row = conn.execute(
            "SELECT * FROM urls WHERE short_code=?",
            (code,)
        ).fetchone()

        if not row:
            raise HTTPException(
                404,
                "short URL not found"
            )

        if (
            row["expires_at"]
            and datetime.fromisoformat(row["expires_at"])
            <= datetime.now(timezone.utc)
        ):
            raise HTTPException(
                410,
                "short URL expired"
            )

        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            UPDATE urls
            SET click_count = click_count + 1
            WHERE short_code=?
            """,
            (code,)
        )

        conn.execute(
            """
            INSERT INTO clicks(
                short_code,
                clicked_at
            )
            VALUES (?, ?)
            """,
            (code, now)
        )

        conn.commit()

        return {
            "redirect_to": row["original_url"]
        }

    finally:
        conn.close()


@app.get("/api/urls/{code}/analytics")
def analytics(code: str):

    conn = get_db()

    try:
        row = conn.execute(
            """
            SELECT
                short_code,
                original_url,
                created_at,
                expires_at,
                click_count
            FROM urls
            WHERE short_code=?
            """,
            (code,)
        ).fetchone()

        if not row:
            raise HTTPException(
                404,
                "short URL not found"
            )

        return dict(row)

    finally:
        conn.close()


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


ORCHESTRATION_RUNS = {}


@app.post("/api/orchestrate")
def orchestrate(scenario: str = "greenfield"):

    if scenario not in {
        "greenfield",
        "brownfield",
        "ambiguous"
    }:
        raise HTTPException(
            400,
            "scenario must be greenfield, brownfield, or ambiguous"
        )

    workflow = AgenticOrchestrator(scenario)

    result = workflow.run()

    ORCHESTRATION_RUNS[workflow.run_id] = workflow

    return result


@app.get("/api/orchestrate/{run_id}")
def get_orchestration(run_id: str):

    workflow = ORCHESTRATION_RUNS.get(run_id)

    if not workflow:
        raise HTTPException(
            404,
            "orchestration run not found"
        )

    return workflow.snapshot()


@app.post("/api/orchestrate/{run_id}/approve")
def approve_orchestration(run_id: str):

    workflow = ORCHESTRATION_RUNS.get(run_id)

    if not workflow:
        raise HTTPException(
            404,
            "orchestration run not found"
        )

    if not workflow.approve_release():

        raise HTTPException(
            409,
            "run is not awaiting release approval"
        )

    return workflow.snapshot()


@app.post("/api/orchestrate/{run_id}/replan")
def replan_orchestration(
    run_id: str,
    reason: str
):

    workflow = ORCHESTRATION_RUNS.get(run_id)

    if not workflow:
        raise HTTPException(
            404,
            "orchestration run not found"
        )

    return workflow.replan(reason)