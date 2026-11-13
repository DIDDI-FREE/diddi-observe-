# DiddiObserve

Implementation of the plan approved in this task and DIDDI Observability v1.

## Scope

Local, versioned Compose stack: Grafana, Prometheus, Loki, Tempo, Alloy, TLS ingestion gateway, blackbox probes and registry exporter. Six provisioned dashboards. Registry-driven, authenticated onboarding; no production target enabled by default. Local synthetic integration test. Publish to the user-provided Git repository on main. No Portainer deployment or mutation.

## Boundaries

Only this repository and explicitly named local test containers may be changed. No Docker socket access by default. Never commit credentials, raw operational logs, audit clones or private inventory. The existing protocol is the source of truth; implementation limitations must be documented.

## Verification

`python -m unittest discover -s tests -v`

`python scripts/render.py --check`

`python scripts/bootstrap.py --demo`

`docker compose --env-file .env -f compose.yaml -f compose.demo.yaml config --quiet`

`docker compose --env-file .env -f compose.yaml -f compose.demo.yaml up -d`

`python scripts/smoke.py`

## Acceptance

The synthetic authenticated signal reaches each backend and Grafana. Unauthorized ingestion is refused; supplied identity is overwritten by trusted registration. All application registrations remain inventoried until evidence of connection exists. Production onboarding, notification destinations, object storage and HA remain explicit deployment decisions.
