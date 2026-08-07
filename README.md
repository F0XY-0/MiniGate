# MiniGate

A lightweight API Gateway / Reverse Proxy built from scratch in pure Python — no off-the-shelf gateway libraries. The goal is to understand what's actually happening in tools like Kong, Nginx, or AWS API Gateway by building the core mechanics yourself.

## What it does

MiniGate sits in front of one or more backend APIs and handles cross-cutting concerns:

- **Reverse proxy** — forwards incoming requests to backend services and returns the response
- **Rate limiting** — token bucket / sliding window algorithms implemented manually
- **Auth layer** — API key validation, then JWT validation
- **Caching** — Redis-backed response caching with TTL and invalidation
- **Load balancing** — round robin / least-connections across multiple backend instances
- **Circuit breaker** — stops routing to a backend after repeated failures, with a cooldown period
- **Observability** — request logging, latency tracking, `/metrics` endpoint (Prometheus format)

## Build order (milestones)

1. Basic reverse proxy — forward to a single hardcoded backend
2. Rate limiting — per-client request limits
3. API key auth — reject unauthenticated requests
4. JWT auth — swap/extend API key auth with token validation
5. Redis caching — cache GET responses
6. Load balancing — route across multiple dummy backend instances
7. Circuit breaker — detect failing backends and stop routing to them temporarily
8. Observability — structured logs, latency tracking, `/metrics` endpoint

Each milestone should work standalone before moving to the next.

## Tech stack

- Python 3.11+
- `asyncio` + `aiohttp` for the async proxy core
- `redis-py` for rate limit state and caching
- `PyJWT` for JWT validation
- Dummy backend services (Flask or Django) to route traffic to during development
- `pytest` for tests

## Project structure

See `FILE_STRUCTURE.md` / folder layout below.

## Running locally

```bash
# create virtualenv
python -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# start redis (required for rate limiting/caching)
docker run -p 6379:6379 redis

# start a dummy backend to test against
python backends/dummy_backend.py --port 9001

# start the gateway
python -m minigate.main
```

## Configuration

Gateway behavior (rate limits, backend targets, auth mode, cache TTL) is defined in `config.yaml`. See `config.example.yaml` for the format.

## Status

🚧 Work in progress — building incrementally, milestone by milestone.
