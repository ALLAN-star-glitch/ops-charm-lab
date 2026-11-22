# Holistic Juju Charm Lab (`ops` Framework & Pebble)

A self-contained Python charm prototype demonstrating holistic state reconciliation, Pebble service layer management, relation data handling, and in-memory unit testing with `ops.testing.Harness` and `pytest`.

## Repository Structure

```text
python-ops-lab/
├── charmcraft.yaml     # Charmcraft platform and configuration specification
├── metadata.yaml       # Charm identity, workload container ('web'), and required relation ('db')
├── config.yaml         # Configurable runtime options ('port', default: 8080)
├── src/
│   └── charm.py        # Event-driven DemoWebAppCharm using holistic _reconcile()
└── test_charm.py       # Unit tests using ops.testing.Harness and pytest
```

## Architecture & Reconciliation Flow

All lifecycle, configuration, and relation events route into a single idempotent `_reconcile()` handler:

```text
Juju Events:
  • web_pebble_ready
  • config_changed      ──▶  _reconcile()  ──▶  1. Verify Pebble socket is reachable
  • db_relation_changed                         2. Verify 'db' relation & URI exist
  • db_relation_broken                          3. Validate 'port' configuration
                                                4. Push Pebble layer & container.replan()
                                                5. Set unit status (Blocked / Waiting / Active)
```

## Running & Testing

```bash
python3 -m venv venv
source venv/bin/activate
pip install ops pytest
pytest -v
```
