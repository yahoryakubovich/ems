# EMS

Backend for equipment management with a simple Clean Architecture layout.

## Stack

- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- Docker Compose

## Project structure

```text
src/app/
  domain/           # entities, enums, business rules
  application/      # commands, filters, ports, services
  infrastructure/   # config, db, repositories, unit of work
  presentation/     # api, routers, schemas, dependencies
alembic/            # migrations
tests/              # domain, application, presentation tests
```

## Domain model

### Category

- `id`
- `name`
- `description`
- `created_at`
- `updated_at`

Rules:

- name is required
- name must be unique
- category cannot be deleted if equipment exists in it

### Equipment

- `id`
- `inventory_number`
- `name`
- `category_id`
- `status`
- `assigned_to_employee_id`
- `serial_number`
- `purchase_date`
- `purchase_cost`
- `notes`
- `created_at`
- `updated_at`

Statuses:

- `in_stock`
- `assigned`
- `maintenance`
- `retired`

Rules:

- inventory number is required and unique
- assigned equipment must have an employee
- assigned equipment cannot change lifecycle status through regular update
- transfer must use a dedicated endpoint
- retired equipment is terminal
- assigned equipment cannot be deleted
- equipment with movement history cannot be deleted

### EquipmentMovement

- `id`
- `equipment_id`
- `movement_type`
- `from_employee_id`
- `to_employee_id`
- `happened_at`
- `comment`
- `created_at`

Movement types:

- `assign`
- `transfer`
- `unassign`

## Environment variables

Copy the template:

```bash
copy .env.example .env
```

Available variables:

```env
APP_NAME=Equipment Management System
APP_VERSION=1.0.0
APP_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ems

POSTGRES_DB=ems
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
```

## Run locally without Docker

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -e .
```

### 2. Start PostgreSQL

You can use a local PostgreSQL instance or start only the DB from compose:

```bash
docker compose up -d db
```

### 3. Apply migrations

```bash
alembic upgrade head
```

### 4. Start the app

```bash
uvicorn main:app --reload
```

App URLs:

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Run with Docker Compose

Build and start everything:

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up -d --build
```

Stop:

```bash
docker compose down
```

Stop and remove database volume:

```bash
docker compose down -v
```

The app container runs migrations on startup:

```text
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000
```

## Migrations

Apply migrations:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "describe change"
```

## Tests

```bash
pytest -q
```

## Seed demo data

If you want the API to have real content right away, load demo data:

```bash
python seed_demo.py
```

Recreate the demo dataset from scratch:

```bash
python seed_demo.py --reset
```

What gets created:

- 4 categories
- 5 equipment items
- assigned, transferred, unassigned history examples
- equipment in `in_stock`, `assigned`, `maintenance`, `retired`

If you run inside Docker:

```bash
docker compose exec app python seed_demo.py --reset
```

At the moment the suite covers:

- domain rules for equipment state
- application service behavior
- API endpoints for assign, transfer, unassign, history

## Main API endpoints

### Categories

- `GET /categories/`
- `GET /categories/{category_id}`
- `POST /categories/`
- `PUT /categories/{category_id}`
- `DELETE /categories/{category_id}`

### Equipments

- `GET /equipments/`
- `GET /equipments/{equipment_id}`
- `POST /equipments/`
- `PUT /equipments/{equipment_id}`
- `DELETE /equipments/{equipment_id}`
- `POST /equipments/{equipment_id}/assign`
- `POST /equipments/{equipment_id}/transfer`
- `POST /equipments/{equipment_id}/unassign`
- `GET /equipments/{equipment_id}/history`

## Example flow

Create a category:

```json
POST /categories/
{
  "name": "Laptops",
  "description": "Portable workstations"
}
```

Create equipment:

```json
POST /equipments/
{
  "inventory_number": "LT-001",
  "name": "MacBook Pro 14",
  "category_id": 1,
  "serial_number": "SN-001",
  "purchase_cost_amount": 2499.99,
  "purchase_cost_currency": "USD",
  "notes": "For design team"
}
```

Assign equipment:

```json
POST /equipments/1/assign
{
  "employee_id": 101,
  "comment": "Issued to employee"
}
```

Transfer equipment:

```json
POST /equipments/1/transfer
{
  "to_employee_id": 205,
  "comment": "Team transfer"
}
```

Unassign equipment:

```json
POST /equipments/1/unassign
{
  "comment": "Returned to stock"
}
```

## Next steps

- add integration tests against real PostgreSQL
- add CI pipeline
- introduce employee context if the domain grows
