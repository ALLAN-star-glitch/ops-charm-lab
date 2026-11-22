#### Holistic Juju Charm Lab (ops Framework & Pebble)

A self-contained Python charm prototype demonstrating holistic state reconciliation, Pebble service layer management, relation data handling, and in-memory unit testing with ops.testing.Harness and pytest. 

#### Repository Structure

Show Code

Hide Code

Download diagram SVG

ASCII

python-ops-lab/
├── charmcraft.yaml     # Charmcraft platform and configuration specification
├── metadata.yaml       # Charm identity, workload container ('web'), and required relation ('db')
├── config.yaml         # Configurable runtime options ('port', default: 8080)
├── src/
│   └── charm.py        # Event-driven DemoWebAppCharm using holistic _reconcile()
└── test_charm.py       # Unit tests using ops.testing.Harness and pytest

Use code with caution.

Copy code text to clipboard.

**Note:** Keep charm.py inside src/ and metadata.yaml / config.yaml in the project root. ops.testing.Harness resolves metadata relative to Path(charm_file).parent.parent. 

#### Architecture & Reconciliation Flow

All lifecycle, configuration, and relation events route into a single idempotent _reconcile() handler: 

text

Juju Events:
  • web_pebble_ready
  • config_changed      ──▶  _reconcile()  ──▶  1. Verify Pebble socket is reachable
  • db_relation_changed                         2. Verify 'db' relation & URI exist
  • db_relation_broken                          3. Validate 'port' configuration
                                                4. Push Pebble layer & container.replan()
                                                5. Set unit status (Blocked / Waiting / Active)

Use code with caution.

Copy code text to clipboard.

#### Lab Instructions

#### 1. Clone & Set Up Virtual Environment

bash

git clone https://github.com/ALLAN-star-glitch/holistic-charm-lab.git
cd holistic-charm-lab

python3 -m venv venv
source venv/bin/activate
pip install ops pytest

Use code with caution.

Copy code text to clipboard.

#### 2. Inspect the Charm Lifecycle (src/charm.py)

Review how DemoWebAppCharm converges toward desired state on every event: 

* **Pebble Readiness:** Checks container.can_connect() before pushing layers; sets WaitingStatus if the sidecar socket is unavailable.
* **Relation Guard:** Verifies the db relation exists (BlockedStatus if missing) and waits for the uri key in the application databag (WaitingStatus until published).
* **Idempotent Replan:** Pushes the Pebble service layer with DATABASE_URL and --port and calls container.replan(), restarting the process only when configuration changes.

#### 3. Run the In-Memory Test Suite (test_charm.py)

Execute pytest to simulate Juju controller events without requiring a live Kubernetes cluster: 

bash

pytest -v

Use code with caution.

Copy code text to clipboard.

#### 4. What Each Test Verifies

* **test_blocks_when_db_relation_missing:** Emits web_pebble_ready with no database integrated and asserts BlockedStatus.
* **test_active_and_reconciles_pebble_when_db_provided:** Simulates juju integrate with postgresql-k8s, publishes a database uri, and verifies ActiveStatus along with the generated Pebble service plan (DATABASE_URL and --port=8080).
* **test_config_change_updates_port:** Updates port to 9090 and verifies Pebble dynamically replans the service command to --port=9090.