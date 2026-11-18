# aClick

A working MVP for a unified digital healthcare platform with patient, partner, and administrator experiences.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Patient | patient@aclick.demo | password |
| Partner | partner@aclick.demo | password |
| Doctor | doctor@aclick.demo | password |
| Ambulance | ambulance@aclick.demo | password |
| Admin | admin@aclick.demo | password |

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest
```

## Production notes

This MVP is for demonstration and validation. Before real patient use, replace SQLite and demo authentication with PostgreSQL and a hardened identity provider, add managed storage, consent flows, payment, SMS, maps, video and security/backup infrastructure, and complete a qualified regulatory/privacy review.
