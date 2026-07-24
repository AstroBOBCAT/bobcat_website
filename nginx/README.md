# `nginx/` — reverse proxy / edge configuration

Configures the `nginx` service in `docker-compose.yml`, which is the single
entry point for the whole stack. It listens on port **80** and routes requests
to the right backend service, adds rate limiting, and forwards the headers the
apps need.

## What's here

- **`nginx.conf`** — mounted into the stock `nginx:alpine` image (the service
  uses `image:`, not a build). It defines:
  - **Rate-limit zones** (`limit_req_zone`, keyed by client IP):
    - `tap_zone` (10 r/s) for the query endpoints that execute user-supplied
      ADQL/SQL — the expensive, abusable surface.
    - `site_zone` (30 r/s) for everything else.
    - Over-budget requests get **HTTP 429** (instead of the default 503) so
      clients can tell throttling from an outage.
  - **Routing:**
    | Path prefix | Proxied to | Purpose |
    |---|---|---|
    | `/tap` | `dachs:8080` | IVOA TAP endpoints (`/tap/sync`, `/tap/async`, `/tap/tables`, …) |
    | `/__system__` | `dachs:8080` | DaCHS's canonical service paths — async TAP job URLs live here, so standard clients break without this route |
    | `/` (everything else) | `backend:8000` | Django site + the SQL/ADQL query form |
  - **Proxy headers** (`Host`, `X-Real-IP`, `X-Forwarded-For`,
    `X-Forwarded-Proto`) and long read/send timeouts (300s on TAP, since async
    ADQL jobs can run a while).

## Notes

- **No TLS here.** This config only terminates plain HTTP on port 80. For a
  real deployment, HTTPS is terminated upstream (a load balancer or an
  nginx TLS listener added here); Django's `DJANGO_BEHIND_TLS` flag exists to
  turn on secure-cookie / HSTS behavior once that's in place. See
  `SECURITY_TODO.md`.
- `X-Forwarded-Proto` is forwarded so Django can honor `SECURE_PROXY_SSL_HEADER`
  when TLS is added upstream.
