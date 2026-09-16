import os
import sqlite3

from fastapi.testclient import TestClient

from app.main import app


DB = "urls.db"


def reset_database():
    if os.path.exists(DB):
        os.remove(DB)

    conn = sqlite3.connect(DB)

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
    conn.close()


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_create_and_analytics():
    reset_database()

    with TestClient(app) as client:
        response = client.post(
            "/api/urls",
            json={"url": "https://example.com/a"},
        )

        assert response.status_code == 201

        code = response.json()["short_code"]

        redirect = client.get(f"/r/{code}")

        assert redirect.status_code == 200
        assert redirect.json()["redirect_to"] == "https://example.com/a"

        analytics = client.get(
            f"/api/urls/{code}/analytics"
        )

        assert analytics.status_code == 200
        assert analytics.json()["click_count"] == 1


def test_duplicate_alias():
    reset_database()

    payload = {
        "url": "https://example.com",
        "custom_alias": "demo",
    }

    with TestClient(app) as client:
        first = client.post("/api/urls", json=payload)
        second = client.post("/api/urls", json=payload)

        assert first.status_code == 201
        assert second.status_code == 409


def test_expired_url():
    reset_database()

    with TestClient(app) as client:
        response = client.post(
            "/api/urls",
            json={
                "url": "https://example.com",
                "expires_at": "2020-01-01T00:00:00Z",
            },
        )

        assert response.status_code == 201

        code = response.json()["short_code"]

        expired = client.get(f"/r/{code}")

        assert expired.status_code == 410


def test_invalid_custom_alias():
    reset_database()

    with TestClient(app) as client:
        response = client.post(
            "/api/urls",
            json={
                "url": "https://example.com",
                "custom_alias": "ab",
            },
        )

        assert response.status_code == 400


def test_missing_short_url():
    reset_database()

    with TestClient(app) as client:
        response = client.get("/r/does-not-exist")

        assert response.status_code == 404