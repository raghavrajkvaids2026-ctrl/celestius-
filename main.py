"""Celestius - Backend Development Workshop registration API."""
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database import get_connection, init_db
from schemas import RegistrationIn, RegistrationOut

EVENT = {
    "name": "Backend Development Workshop",
    "date": "2026-10-20",
    "capacity": 50,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Celestius Event Registration API", lifespan=lifespan)


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"error": "error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    problems = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "problem": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_input", "message": "Invalid or missing information", "details": problems},
    )


def require_admin(x_api_key: str = Header(default=None)):
    """Organizer endpoints need X-API-Key when ADMIN_API_KEY is set in the environment."""
    expected = os.environ.get("ADMIN_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(401, {"error": "unauthorized", "message": "Missing or invalid X-API-Key"})


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


@app.get("/")
def event_info():
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    finally:
        conn.close()
    return {**EVENT, "registered": count, "seats_left": EVENT["capacity"] - count}


@app.post("/register", response_model=RegistrationOut, status_code=201)
def register(payload: RegistrationIn):
    conn = get_connection()
    try:
        # BEGIN IMMEDIATE takes the write lock up front, so "count then insert"
        # is atomic: two simultaneous requests can't both grab seat #50.
        conn.execute("BEGIN IMMEDIATE")
        try:
            count = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
            if count >= EVENT["capacity"]:
                conn.execute("ROLLBACK")
                return error(409, "event_full", "Event is full")

            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            cur = conn.execute(
                "INSERT INTO registrations (name, email, college, department, registered_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (payload.name, payload.email, payload.college, payload.department, now),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            return error(409, "duplicate_registration", "This email is already registered")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        row = conn.execute("SELECT * FROM registrations WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


@app.get("/registrations", response_model=List[RegistrationOut], dependencies=[Depends(require_admin)])
def list_registrations():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM registrations ORDER BY id").fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/registrations/email/{email}", response_model=RegistrationOut, dependencies=[Depends(require_admin)])
def get_by_email(email: str):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM registrations WHERE email = ?", (email.strip().lower(),)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(404, {"error": "not_found", "message": "Registration not found"})
    return row_to_dict(row)


@app.get("/registrations/{reg_id}", response_model=RegistrationOut, dependencies=[Depends(require_admin)])
def get_registration(reg_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM registrations WHERE id = ?", (reg_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(404, {"error": "not_found", "message": "Registration not found"})
    return row_to_dict(row)
