# API Documentation

All endpoints return the same JSON envelope:

```json
// Success
{ "success": true, "message": "...", "data": { } }
// Error
{ "success": false, "message": "...", "errors": { } }
```

All endpoints except `/api/auth/login` and `/api/health` require a Bearer
JWT: `Authorization: Bearer <token>`.

## Auth

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/login` | `{email, password}` → access token + user |
| POST | `/api/auth/logout` | Client discards token (stateless JWT) |
| GET | `/api/auth/me` | Current user |

## Issues

| Method | Path | Roles | Notes |
|---|---|---|---|
| POST | `/api/issues` | any authenticated | Creates issue; auto-runs AI classification, priority prediction, similarity check, impact assessment |
| GET | `/api/issues` | any | Filters: `status`, `priority`, `vehicle_id`, `hub_id`, `search`; pagination: `page`, `per_page` |
| GET | `/api/issues/<id>` | any | Full detail incl. AI suggestions, impact, similar issues, history, comments |
| PUT | `/api/issues/<id>` | any | Edit title/description |
| DELETE | `/api/issues/<id>` | any | Deletes issue |
| POST | `/api/issues/<id>/status` | any | Body: `{status}`. Rejects invalid transitions (400) |
| POST | `/api/issues/<id>/priority` | any | Body: `{priority, reason?}`. Logs override reason |
| POST | `/api/issues/<id>/assign` | any | Body: `{team_id?, user_id?}`. Auto-moves OPEN → ASSIGNED |
| POST | `/api/issues/<id>/comments` | any | Body: `{comment}` |

## AI

| Method | Path | Notes |
|---|---|---|
| POST | `/api/ai/classify` | `{title, description}` → predicted category + confidence. 503 if model not trained |
| POST | `/api/ai/priority` | `{title, description, category}` → predicted priority + confidence |
| POST | `/api/ai/similarity` | `{title, description, exclude_issue_id?}` → potentially related issues |
| GET | `/api/ai/issues/<id>/ai-analysis` | Latest stored AI prediction for an issue |
| GET | `/api/ai/issues/<id>/impact-analysis` | Recomputes operational impact on demand |
| POST | `/api/ai/issues/<id>/priority-override` | `{priority, reason}` — explicit manager override, audit-logged |

## Fleet

| Resource | Endpoints |
|---|---|
| Vehicles | `GET/POST /api/vehicles`, `GET /api/vehicles/<id>` (incl. recent issues + maintenance), `PUT /api/vehicles/<id>` |
| Drivers | `GET/POST /api/drivers`, `GET/PUT /api/drivers/<id>` |
| Hubs | `GET/POST /api/hubs`, `GET /api/hubs/<id>` (incl. open/critical issue counts), `PUT /api/hubs/<id>` |
| Charging | `GET/POST /api/charging/stations`, `PUT /api/charging/stations/<id>`, `POST /api/charging/sessions`, `POST /api/charging/sessions/<id>/end` |
| Maintenance | `GET/POST /api/maintenance`, `PUT /api/maintenance/<id>` |

Vehicle/driver/hub creation is Admin-only; status updates allow Admin + Ops
Manager (+ Maintenance for charging stations and maintenance records).

## Analytics

| Method | Path | Notes |
|---|---|---|
| GET | `/api/analytics/overview` | KPI cards |
| GET | `/api/analytics/issues` | By category/priority/status/hub + 30-day trend. Supports `start_date`, `end_date`, `hub_id`, `category`, `priority`, `status`, `vehicle_id` filters |
| GET | `/api/analytics/vehicles` | Top vehicles by issue count, vehicles by status |
| GET | `/api/analytics/hubs` | Issues by hub |
| GET | `/api/analytics/recurring-issues` | Vehicle+category patterns exceeding `min_occurrences` in `window_days` |

## Notifications & Audit

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/api/notifications` | any | Own notifications + unread count |
| POST | `/api/notifications/<id>/read` | any | Mark one as read |
| POST | `/api/notifications/read-all` | any | Mark all as read |
| GET | `/api/audit-logs` | **admin only** | Paginated audit trail |

## Users (Admin)

| Method | Path | Notes |
|---|---|---|
| GET/POST | `/api/users` | List / create users |
| PUT | `/api/users/<id>` | Update role/team/active status |
| GET | `/api/users/roles` | List roles |
| GET | `/api/users/teams` | List teams |

## HTTP Status Codes Used

`200` OK · `201` Created · `400` Bad Request (validation) · `401` Unauthorized
(missing/invalid token) · `403` Forbidden (wrong role) · `404` Not Found ·
`409` Conflict (duplicate, invalid state) · `503` Service Unavailable
(ML model not yet trained) · `500` Internal Server Error (unhandled,
generic message only — no stack traces returned to the client)
