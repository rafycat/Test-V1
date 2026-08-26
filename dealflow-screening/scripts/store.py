"""
store.py — persistance SQLite pour le screening de deal flow.

Rôle : dédoublonner les sociétés entre deux exécutions du pipeline, et garder
un historique des signaux détectés (pour ne ressortir que le NOUVEAU signal,
pas la société entière à chaque run).
"""
from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "companies_seen.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,            -- SIREN pour la France, ou clé composite pays+nom sinon
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    sector TEXT NOT NULL,
    naf_code TEXT,
    creation_date TEXT,
    employees_range TEXT,
    revenue_eur REAL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_score REAL,
    raw_json TEXT                    -- snapshot complet pour audit / debug
);

CREATE TABLE IF NOT EXISTS signals (
    company_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,       -- ex: "funding", "patent", "headcount_growth"
    detail TEXT,
    detected_at TEXT NOT NULL,
    source TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX IF NOT EXISTS idx_signals_company ON signals(company_id);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_company(conn: sqlite3.Connection, company: dict) -> bool:
    """
    Insère ou met à jour une société. Retourne True si c'est une NOUVELLE
    société (jamais vue), False si elle était déjà connue (mise à jour seule).
    `company` doit contenir au minimum: id, name, country, sector.
    """
    cur = conn.cursor()
    cur.execute("SELECT id FROM companies WHERE id = ?", (company["id"],))
    exists = cur.fetchone() is not None
    now = _now()
    sector = company.get("sector") or company.get("sector_guess") or "unknown"

    if exists:
        cur.execute(
            """UPDATE companies SET
                 last_seen_at = ?,
                 last_score = ?,
                 employees_range = COALESCE(?, employees_range),
                 revenue_eur = COALESCE(?, revenue_eur),
                 raw_json = ?
               WHERE id = ?""",
            (
                now,
                company.get("score"),
                company.get("employees_range"),
                company.get("revenue_eur"),
                json.dumps(company, ensure_ascii=False),
                company["id"],
            ),
        )
    else:
        cur.execute(
            """INSERT INTO companies
                 (id, name, country, sector, naf_code, creation_date,
                  employees_range, revenue_eur, first_seen_at, last_seen_at,
                  last_score, raw_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                company["id"],
                company["name"],
                company["country"],
                sector,
                company.get("naf_code"),
                company.get("creation_date"),
                company.get("employees_range"),
                company.get("revenue_eur"),
                now,
                now,
                company.get("score"),
                json.dumps(company, ensure_ascii=False),
            ),
        )
    conn.commit()
    return not exists


def add_signal(conn: sqlite3.Connection, company_id: str, signal_type: str,
               detail: str, source: str) -> None:
    conn.execute(
        "INSERT INTO signals (company_id, signal_type, detail, detected_at, source) "
        "VALUES (?, ?, ?, ?, ?)",
        (company_id, signal_type, detail, _now(), source),
    )
    conn.commit()


def has_signal_since(conn: sqlite3.Connection, company_id: str, signal_type: str,
                      since_iso: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM signals WHERE company_id = ? AND signal_type = ? "
        "AND detected_at >= ? LIMIT 1",
        (company_id, signal_type, since_iso),
    )
    return cur.fetchone() is not None


def get_company(conn: sqlite3.Connection, company_id: str) -> Optional[dict]:
    cur = conn.execute("SELECT raw_json FROM companies WHERE id = ?", (company_id,))
    row = cur.fetchone()
    return json.loads(row[0]) if row else None
