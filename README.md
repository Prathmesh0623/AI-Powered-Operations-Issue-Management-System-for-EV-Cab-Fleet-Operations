# AI-Powered Operations & Issue Management System

Intelligent issue detection, prioritization, tracking, and operational impact
analysis for fleet operations teams — built as a full-stack prototype
demonstrating Python, Flask, PostgreSQL, Machine Learning, NLP, and
production-style engineering practices.

## Problem Statement

Operations teams handling EV fleets receive a constant stream of issues —
vehicle breakdowns, charging failures, driver problems, customer complaints —
and struggle to triage, prioritize, deduplicate, and assign them manually at
scale. This system provides AI-assisted decision support (classification,
priority prediction, duplicate detection, operational impact scoring) while
keeping a human operations manager as the final decision maker at every step.

**All data in this project is synthetic**, generated for prototype/training
purposes. No real company, fleet, or customer data is used or claimed.

## Core Design Principle: AI as Decision Support

The system never auto-assigns, auto-resolves, or auto-merges. Every AI output
(predicted category, predicted priority, similarity match, operational
impact) is surfaced as a **suggestion** the operations manager reviews,
accepts, or overrides — with the override reason stored for transparency.

## Features

- Role-based access (Admin, Operations Manager, Operator, Maintenance/Support)
- Full issue lifecycle management (OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED, with validated transitions)
- Fleet management: vehicles, drivers, hubs, charging stations, maintenance records
- AI issue classification (TF-IDF + Logistic Regression)
- AI priority prediction (text + category features)
- NLP duplicate/similarity detection (TF-IDF + cosine similarity)
- Rule-based, explainable operational impact scoring
- Analytics dashboard (KPIs, charts, recurring-issue pattern detection)
- In-app notifications and a full audit log
- JWT authentication with hashed passwords

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, Flask-SQLAlchemy, Flask-JWT-Extended |
| Database | PostgreSQL (SQLite supported for local dev) |
| ML/NLP | scikit-learn, pandas, numpy (TF-IDF, Logistic Regression, Random Forest, cosine similarity) |
| Frontend | HTML5, vanilla JavaScript, Chart.js |
| Testing | Pytest |

## Project Structure

See `docs/architecture.md` for the full layered architecture and folder layout.

## Installation

```bash
git clone <this-repo>
cd ai-operations-management
python -m venv venv
# Windows: venv\Scripts\Activate.ps1   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Environment Setup

```bash
cp .env.example .env
```

By default `DATABASE_URL` points at a local SQLite file so the project runs
immediately with no extra setup. For PostgreSQL, set:

```
DATABASE_URL=postgresql://username:password@localhost:5432/ai_ops_db
```

## Database Setup

```bash
python database/seed_data.py
```

This creates all tables and seeds baseline roles, teams, issue categories,
demo users, and a small demo fleet. Printed demo logins:

| Role | Email | Password |
|---|---|---|
| Admin | admin@demo.com | Admin@123 |
| Operations Manager | manager@demo.com | Manager@123 |
| Operator | operator@demo.com | Operator@123 |
| Maintenance | support@demo.com | Support@123 |

## Training the ML Models

**Models are not pre-shipped in this repo** — scikit-learn does not
guarantee that a `.pkl` file trained on one version will load correctly on
another (this was confirmed the hard way: a model trained with scikit-learn
1.9.1 failed with `AttributeError: 'LogisticRegression' object has no
attribute 'multi_class'` when loaded under 1.5.0). Train them locally after
installing `requirements.txt`, so they match your exact installed version:

```bash
python ml/data/generate_dataset.py   # generates the synthetic dataset
python ml/data/eda.py                # inspect class balance
python ml/training/train_category.py
python ml/training/train_priority.py
```

The app degrades gracefully if these haven't been run yet — AI endpoints
return `503` instead of crashing — but issue creation calls them
automatically, so training them first is the right first step after setup.

See `docs/ml.md` for an honest discussion of what these models can and
cannot currently do given synthetic training data.

## Running the Application

```bash
python run.py
```

Visit `http://127.0.0.1:5000/login`.

## Running Tests

```bash
pytest tests/ -v
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture, layers, folder structure
- [`docs/database.md`](docs/database.md) — schema, relationships, constraints
- [`docs/api.md`](docs/api.md) — full REST API reference
- [`docs/ml.md`](docs/ml.md) — ML/NLP approach, evaluation, honest limitations
- [`docs/testing.md`](docs/testing.md) — test strategy and coverage
- [`docs/deployment.md`](docs/deployment.md) — production deployment guide

## Screenshots

_(Add screenshots of the Dashboard, Issue Details, and Analytics pages here
before sharing this project externally.)_

## Limitations

- All data is synthetic; no real fleet, customer, or company data.
- The priority-prediction model currently performs close to random-baseline
  because priority in the synthetic dataset was assigned independently of any
  real signal. Real predictive value would require structured operational
  features (vehicle availability, shift dependency, backup counts) — the
  Operational Impact Engine (rule-based) currently fills that gap.
- Similarity detection surfaces "potentially related" issues; it never
  confirms duplicates. Merging remains a manual decision.
- The Operational Impact Engine is deliberately rule-based, not ML, so its
  reasoning stays fully auditable.
- Real-time fleet telemetry, IoT integration, and production-scale data
  volumes are outside this prototype's scope.

## Future Enhancements

- Real-time vehicle telemetry / IoT integration
- Transformer-based embeddings for similarity search
- Predictive maintenance
- Email/SMS notification channels
- Model retraining pipeline / MLOps
- Cloud deployment with monitoring
