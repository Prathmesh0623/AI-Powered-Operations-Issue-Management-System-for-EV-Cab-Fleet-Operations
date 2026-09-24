# Architecture

## Layered Design

```
Frontend (HTML/CSS/JS + Chart.js)
        │  fetch (JSON)
        ▼
REST API Layer (Flask blueprints/routes)
        │
        ▼
Service Layer (issue_service, impact_service, notification_service, audit_service)
        │
        ▼
AI Layer (category_predictor, priority_predictor, similarity_engine)
        │
        ▼
Models / SQLAlchemy ORM
        │
        ▼
Database (PostgreSQL / SQLite)
```

Routes never talk to the database directly for anything beyond simple reads —
business logic (status transitions, AI suggestion generation, notifications)
lives in `services/`, keeping routes thin and testable.

## Request Flow Example — Creating an Issue

1. `POST /api/issues` hits `routes/issue_routes.py::create_issue`
2. Delegates to `services/issue_service.py::create_issue`
3. Which, in sequence:
   - Validates and persists the issue (`status=OPEN`)
   - Records the initial history entry
   - Calls the category/priority predictors (`ml/inference/`) and stores results as *suggestions* (never overwrites the manager-facing fields)
   - Runs the similarity engine against recently open issues
   - Runs the rule-based operational impact engine
   - Fires notifications (critical issue, high impact, similarity match) via `notification_service`
4. Returns the created issue as JSON

## Folder Structure

```
ai-operations-management/
├── app.py                  # Flask app factory, blueprint registration
├── run.py                  # Entry point
├── config/config.py        # Environment-driven configuration
├── extensions/              # db instance, JWT role decorator
├── models/                  # SQLAlchemy models (one file per entity)
├── routes/                  # Flask blueprints (thin — delegate to services)
├── services/                 # Business logic layer
├── ml/
│   ├── data/                # Synthetic dataset generator + EDA
│   ├── preprocessing/        # Shared text cleaning
│   ├── training/              # Model training scripts
│   ├── inference/             # Lightweight inference wrappers (load-once)
│   ├── models/                 # Saved .pkl model files
│   └── vectorizers/            # Saved .pkl TF-IDF vectorizers
├── database/seed_data.py    # Creates tables + baseline/demo data
├── templates/                # Server-rendered HTML (Jinja2)
├── static/{css,js}/          # Frontend assets
├── tests/                    # Pytest suite
└── docs/                     # This documentation
```

## Why This Structure?

- **Routes stay thin.** Business rules (status transitions, AI suggestion
  handling) live in services, so they're unit-testable without spinning up
  HTTP requests, and reusable across multiple routes.
- **ML inference is decoupled from training.** `ml/inference/*` loads a saved
  model once at import time and exposes a single predict function; it never
  reloads per-request. Training scripts (`ml/training/*`) are standalone and
  run offline.
- **AI outputs never silently overwrite manager-facing fields.** `Issue.priority`
  (what the manager sees and controls) is separate from `Issue.ai_predicted_priority`
  (the suggestion). This is the "AI = decision support, manager = decision
  maker" principle enforced at the data layer, not just in the UI copy.

## AI Layer Detail

```
Issue Text → Preprocessing (ml/preprocessing/text_preprocessing.py)
           → TF-IDF Vectorization
           → Trained Model (Logistic Regression / Random Forest)
           → Prediction + Confidence
           → Stored as suggestion (AIPrediction row + Issue.ai_predicted_*)
           → Surfaced to manager in Issue Details UI
```

The Operational Impact Engine (`services/impact_service.py`) is intentionally
**not** part of this ML pipeline — it's a transparent, rule-based scorer so
every impact rating comes with a human-readable "because..." explanation.
