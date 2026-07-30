# BI Education CRM Demo

A polished Bitrix-style CRM demo for BI Education built with React + TypeScript on the frontend and Django REST Framework on the backend.

## What the demo includes

- Pipeline-aware kanban board for school, kindergarten, and B2B deals
- Branch filtering for Riviera, Quantum STEM, Quantum Tech, and ALDI BI
- One-click lead simulation with toast feedback
- Deal modal with editable parent/child profiles, tariff selection, food/transport toggles, waitlist handling, and a pricing calculator
- Live pricing preview and payment schedule generation using the requested branch formulas
- Drag-and-drop stage updates with optimistic UI behavior

## Tech stack

### Frontend
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Zustand
- Axios
- @dnd-kit
- lucide-react
- react-hot-toast
- date-fns

### Backend
- Django 4.2
- Django REST Framework
- PostgreSQL (Docker)
- SQLite fallback for local development

## Project structure

```text
bi-crm-demo/
├── backend/
│   ├── bi_crm_demo/
│   ├── crm/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── store/
│   │   └── types.ts
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Backend setup

### Local development

```bash
cd bi-crm-demo/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
USE_SQLITE=True python manage.py migrate
USE_SQLITE=True python manage.py generate_mock_data
USE_SQLITE=True python manage.py runserver 0.0.0.0:8000
```

### Key API endpoints

- GET /api/health/
- GET /api/deals/
- GET /api/contacts/
- POST /api/deals/simulate-lead/
- PATCH /api/deals/<id>/

## Frontend setup

```bash
cd bi-crm-demo/frontend
npm install
npm run dev -- --host 0.0.0.0
```

Then open:

- http://localhost:5173/

## Docker setup

```bash
cd bi-crm-demo
docker compose up --build
```

This starts:

- PostgreSQL database service: db
- Django API service: api

The API container runs migrations, generates mock data, and serves the API on port 8000.

## Verification checklist

### Backend

```bash
curl http://127.0.0.1:8000/api/health/
```

Expected response:

```json
{"status": "ok", "service": "bi-crm-demo"}
```

### Frontend

Open http://localhost:5173/ and confirm:

- the pipeline switcher updates the kanban board
- the branch filter narrows the visible deals
- the simulate lead button creates a new deal with a success toast
- dragging a card between columns updates the deal stage instantly
- the deal modal recalculates the pricing preview and refreshes the payment schedule

## Notes

- The Docker version uses PostgreSQL.
- The local fallback uses SQLite for convenience during development.
- The mock data generator creates realistic scenarios across school, kindergarten, and B2B deals.
