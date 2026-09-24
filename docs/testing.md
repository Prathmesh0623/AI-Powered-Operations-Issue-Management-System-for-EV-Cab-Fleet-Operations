# Testing Documentation

## Strategy

Pytest, using Flask's test client against an in-memory SQLite database
(`tests/conftest.py`) — no real database or running server required. Each
test gets a fresh, isolated database via the `app` fixture (`db.create_all()`
before, `db.drop_all()` after).

## Coverage

| File | Covers |
|---|---|
| `test_auth.py` | Login (success/wrong password/missing fields/unknown user), `/auth/me`, protected-route rejection (missing/garbage token) |
| `test_issues.py` | Issue creation (incl. validation), listing, 404 on missing issue, **valid and invalid status transitions**, invalid priority value, empty comment rejection, assignment, operational impact populated on creation |
| `test_vehicles.py` | Listing, detail, 404, RBAC (operator forbidden from creating a vehicle), duplicate registration number, invalid status value, status update |
| `test_ai.py` | Classify/priority validation (missing description), predictions when model is ready (skips gracefully with a 503 assertion if not trained), similarity engine unit tests (near-duplicate match, unrelated text, empty candidates), impact-analysis endpoint |
| `test_analytics.py` | Auth requirement, KPI/breakdown response shape, recurring-issues endpoint, **audit log RBAC (403 for non-admin, 200 for admin)**, notifications endpoint |

**Result at last run: 44/44 tests passing.**

## Edge Cases Explicitly Tested

- Empty/missing required fields (title, description, comment)
- Invalid enum values (priority, vehicle status)
- Invalid state transitions (OPEN → RESOLVED directly)
- Duplicate unique constraints (vehicle registration number)
- Missing/garbage auth tokens
- Wrong-role access to admin-only and role-gated endpoints
- Nonexistent resource IDs (404s)

## Known, Non-Blocking Warnings

The test run currently emits deprecation warnings from:
- SQLAlchemy's legacy `Query.get()` (superseded by `Session.get()` in 2.0-style usage)
- Python's `datetime.utcnow()` (naive UTC, deprecated in favor of timezone-aware objects)
- PyJWT's `InsecureKeyLengthWarning` on the test suite's short dev JWT secret

None of these cause failures; they're flagged here rather than hidden, and
are reasonable cleanup items before a production deployment (see
`docs/deployment.md`).

## Running Tests

```bash
pytest tests/ -v
```

## Not Yet Covered

- Driver, Hub, Charging, and Maintenance route tests (fleet CRUD follows the
  same pattern as `test_vehicles.py` and would be a straightforward
  extension)
- Frontend/UI tests (this project only has backend/API-level automated tests)
- Load/performance testing
