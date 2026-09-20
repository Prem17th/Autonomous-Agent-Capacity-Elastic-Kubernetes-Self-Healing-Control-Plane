# Nasiko Sentinel - Bug Tracker

## Active Bugs
No known bugs currently identified.

---

## Resolved Issues (Phase 2)
- **Resolved (2026-09-20):** Standardized tool metadata exports in `src/tools/__init__.py` to eliminate circular import risk and enable direct tool registry access.
- **Resolved (2026-09-20):** Handled offline Kubernetes environments by returning structured `InfrastructureError` JSON-RPC responses rather than unhandled socket crashes.

---

## Resolved Issues (Phase 1)
- **Resolved (2026-09-20):** Resolved standard library package name shadowing collision by standardizing internal logger package path to `src/logger/`.
- **Resolved (2026-09-20):** Resolved direct script execution `sys.path` resolution in `src/main.py` to allow both `python src/main.py` and `python -m src.main`.
