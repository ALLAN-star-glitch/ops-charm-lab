import ops
import ops.testing
import pytest

from src.charm import DemoWebAppCharm


@pytest.fixture
def harness():
    """Set up an isolated Juju test harness for DemoWebAppCharm."""
    h = ops.testing.Harness(DemoWebAppCharm)
    h.begin()
    yield h
    h.cleanup()


def test_blocks_when_db_relation_missing(harness):
    """Charm should enter BlockedStatus if Pebble is ready but no DB is related."""
    harness.set_can_connect("web", True)
    harness.charm.on.web_pebble_ready.emit(harness.model.unit.get_container("web"))

    assert isinstance(harness.model.unit.status, ops.BlockedStatus)
    assert "Missing required 'db' relation" in harness.model.unit.status.message


def test_active_and_reconciles_pebble_when_db_provided(harness):
    """Charm should configure Pebble and become Active once DB relation provides a URI."""
    harness.set_can_connect("web", True)

    # Simulate 'juju integrate demo-web-app postgresql-k8s'
    rel_id = harness.add_relation("db", "postgresql-k8s")
    harness.add_relation_unit(rel_id, "postgresql-k8s/0")
    harness.update_relation_data(
        rel_id,
        "postgresql-k8s",
        {"uri": "postgres://user:pass@pg:5432/app"},
    )

    # Verify unit status is Active
    assert isinstance(harness.model.unit.status, ops.ActiveStatus)
    assert "Running on port 8080" in harness.model.unit.status.message

    # Verify Pebble service plan received the exact DATABASE_URL and port
    plan = harness.get_container_pebble_plan("web")
    service = plan.services["web"]
    assert service.command == "/usr/local/bin/server --port=8080"
    assert service.environment == {"DATABASE_URL": "postgres://user:pass@pg:5432/app"}
    assert harness.model.unit.get_container("web").get_service("web").is_running()


def test_config_change_updates_port(harness):
    """Updating 'port' config should dynamically replan the Pebble service."""
    harness.set_can_connect("web", True)
    rel_id = harness.add_relation("db", "postgresql-k8s")
    harness.update_relation_data(
        rel_id,
        "postgresql-k8s",
        {"uri": "postgres://user:pass@pg:5432/app"},
    )

    # Simulate 'juju config demo-web-app port=9090'
    harness.update_config({"port": 9090})

    assert isinstance(harness.model.unit.status, ops.ActiveStatus)
    assert "Running on port 9090" in harness.model.unit.status.message
    plan = harness.get_container_pebble_plan("web")
    assert plan.services["web"].command == "/usr/local/bin/server --port=9090"
