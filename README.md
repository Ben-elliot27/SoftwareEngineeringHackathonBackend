# SoftwareEngineeringHackathonBackend

## Frontend authentication guide

This API uses OAuth2 Password Flow with JWT bearer tokens.

### 1) Login and get an access token

Endpoint:
- `POST /api/v1/auth/login`
- Content-Type: `application/x-www-form-urlencoded`
- Send:
  - `username` = user email
  - `password` = user password

Example (frontend `fetch`):

```ts
const form = new URLSearchParams();
form.set("username", email); // email goes in "username"
form.set("password", password);

const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: form.toString(),
});

if (!res.ok) throw new Error("Login failed");
const { access_token, token_type } = await res.json();
// token_type is "bearer"
```

### 2) Send authenticated requests

For protected endpoints, always send:

```http
Authorization: Bearer <access_token>
```

Example helper:

```ts
async function api(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem("access_token");
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
}
```

### 3) Which endpoints require auth and role

#### Public endpoints
- `GET /`
- `GET /health`
- `POST /api/v1/auth/login`

#### Any authenticated user
- `GET /api/v1/users/me`
- `GET /api/v1/users/{id}` (employees only their own profile; managers/admins can view any)
- `GET /api/v1/time-codes/`
- `GET /api/v1/time-codes/{id}`
- `GET /api/v1/timesheets/`
- `GET /api/v1/timesheets/{id}`
- `POST /api/v1/timesheets/`
- `PATCH /api/v1/timesheets/{id}`
- `DELETE /api/v1/timesheets/{id}` (admins can delete any; employees only own pending entries)

#### Manager or admin
- `POST /api/v1/timesheets/{id}/approve`
- `POST /api/v1/timesheets/{id}/reject`

#### Admin only
- `GET /api/v1/users/`
- `POST /api/v1/users/`
- `PATCH /api/v1/users/{id}`
- `DELETE /api/v1/users/{id}`
- `POST /api/v1/time-codes/`
- `PATCH /api/v1/time-codes/{id}`
- `DELETE /api/v1/time-codes/{id}`
- `GET /api/v1/time-codes/{id}/access`
- `POST /api/v1/time-codes/{id}/access/{user_id}`
- `DELETE /api/v1/time-codes/{id}/access/{user_id}`

### 4) Important frontend behavior notes

- Employees only see time codes they are granted.
- Employees can only create timesheets for themselves.
- Approve/reject actions use the authenticated manager/admin identity from the JWT (cannot be spoofed from request body).
- On `401`, redirect to login and request a fresh token.
