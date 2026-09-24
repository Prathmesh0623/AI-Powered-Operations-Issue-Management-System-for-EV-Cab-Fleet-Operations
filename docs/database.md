# Database Documentation

## Engine

PostgreSQL in production; SQLite supported for local development via the
same `DATABASE_URL` environment variable (SQLAlchemy abstracts the
difference). Schema is defined entirely through SQLAlchemy models in
`models/` — there is no hand-written `schema.sql` to keep in sync separately.

## Tables & Relationships

| Table | Purpose | Key relationships |
|---|---|---|
| `roles` | admin / ops_manager / operator / maintenance | 1:N → users |
| `teams` | Assignable teams (e.g. Charging & Maintenance) | 1:N → users, 1:N → issues (assigned_team) |
| `users` | All system users | N:1 → roles, N:1 → teams |
| `hubs` | Physical operations hubs | 1:N → vehicles, drivers, charging_stations, issues |
| `vehicles` | Fleet vehicles | N:1 → hubs; 1:N → issues, maintenance_records, charging_sessions, drivers |
| `drivers` | Fleet drivers | N:1 → hubs, vehicles; 1:N → issues |
| `charging_stations` | Per-hub charging infrastructure | N:1 → hubs; 1:N → charging_sessions |
| `charging_sessions` | Individual charge events | N:1 → charging_stations, vehicles |
| `maintenance_records` | Service history | N:1 → vehicles, issues |
| `issue_categories` | Category lookup (Vehicle, Battery, Charging, …) | 1:N → issues |
| `issues` | Core entity | N:1 → users (reporter, assigned_user), teams, vehicles, drivers, hubs, issue_categories |
| `issue_history` | Field-level change log per issue | N:1 → issues, users |
| `issue_comments` | Comments/resolution notes | N:1 → issues, users |
| `ai_predictions` | Stored AI suggestions (category/priority + confidence) | N:1 → issues |
| `similar_issues` | Similarity match pairs | N:1 → issues (both `issue_id` and `related_issue_id`) |
| `notifications` | In-app notifications | N:1 → users |
| `audit_logs` | Sensitive-action audit trail | N:1 → users (nullable — system actions) |

## Design Conventions

- Every table has an integer primary key `id`.
- `created_at` (and `updated_at` where the row is mutable) default to UTC now.
- Foreign keys are nullable where the relationship is optional (e.g. an issue
  isn't required to reference a vehicle).
- Enumerated fields (`Issue.status`, `Issue.priority`, `Vehicle.status`, etc.)
  are validated in the service/route layer against a Python tuple/set of
  allowed values (see e.g. `models/issue.py::ISSUE_STATUSES`), rather than a
  database-level CHECK constraint, so the same validation logic is reusable
  and unit-testable in Python.
- `Issue.priority` (manager-facing) and `Issue.ai_predicted_priority`
  (AI suggestion) are deliberately separate columns — see `docs/architecture.md`.

## Issue Status Lifecycle (Enforced in `services/issue_service.py`)

```
OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
OPEN → REJECTED
```

`VALID_TRANSITIONS` in `models/issue.py` is the single source of truth;
`issue_service.change_status()` rejects anything not listed there.

## Known Limitation

`SimilarIssue` has two foreign keys into `issues` (`issue_id` and
`related_issue_id`). The reverse relationship `Issue.similar_issues_found` is
marked `viewonly=True` to avoid a SQLAlchemy relationship-overlap warning.
Practical effect: deleting an `Issue` does not cascade-delete its
`SimilarIssue` rows through the ORM. This is a non-issue on SQLite (FKs not
enforced by default) but would raise a foreign-key violation on PostgreSQL
with FKs enabled — worth adding an explicit cascade or cleanup step before
production use.
