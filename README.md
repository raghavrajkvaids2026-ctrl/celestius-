# Celestius Event Registration API

Backend for the **Backend Development Workshop** (20 Oct 2026, capacity 50).
Built with **Python + FastAPI + SQLite**.

## Run it

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

Optional env vars:
- `ADMIN_API_KEY` - if set, organizer endpoints (`GET /registrations...`) require header `X-API-Key: <key>`
- `DB_PATH` - SQLite file location (default `registrations.db`)

## Endpoints

| Method | Route | Purpose |
|---|---|---|
| POST | `/register` | Register a student |
| GET | `/registrations` | List all registrations (organizer) |
| GET | `/registrations/{id}` | One registration by ID (organizer) |
| GET | `/registrations/email/{email}` | One registration by email (organizer) |
| GET | `/` | Event info + seats left |

`POST /register` body:
```json
{"name": "Asha K", "email": "asha@example.com", "college": "VIT", "department": "CSE"}
```
`college` and `department` are optional. `registered_at` is set by the server (UTC).

## Responses

| Situation | Status | `error` |
|---|---|---|
| Registered | 201 | - |
| Duplicate email | 409 | `duplicate_registration` |
| Event full | 409 | `event_full` ("Event is full") |
| Invalid/missing fields | 422 | `invalid_input` (with per-field `details`) |
| Not found | 404 | `not_found` |
| Bad/missing admin key | 401 | `unauthorized` |

## Design decisions (and why)

- **Capacity race condition:** a naive "count, then insert" lets two simultaneous requests both take seat 50. The register route uses `BEGIN IMMEDIATE`, which takes SQLite's write lock before counting, so count + insert is atomic. `tests/test_api.py` fires 80 parallel requests and asserts exactly 50 succeed.
- **Duplicates:** enforced by a `UNIQUE COLLATE NOCASE` constraint on email in the database, not just an app-level check, so it holds even under concurrency. Emails are also lowercased before saving.
- **Validation:** Pydantic models trim and check input; errors come back in one consistent JSON shape.
- **Plain `sqlite3`, parameterized queries:** no ORM, so every query is visible and SQL-injection safe.

## Tests

```bash
python -m pytest -q
```

## Project layout

```
main.py        routes + capacity/duplicate logic
database.py    SQLite connection + table creation
schemas.py     request/response models and validation
tests/         API tests
```

## Possible improvements

Pagination for `/registrations`, a waitlist when full, cancel-registration endpoint, PostgreSQL + migrations for production, rate limiting on `/register`.
