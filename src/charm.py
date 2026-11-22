#!/usr/bin/env python3
import logging
import ops

logger = logging.getLogger(__name__)


class DemoWebAppCharm(ops.CharmBase):
    """Holistic Juju charm managing a web workload via Pebble and a PostgreSQL relation."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        # Observe lifecycle, config, Pebble container, and relation events
        framework.observe(self.on.web_pebble_ready, self._reconcile)
        framework.observe(self.on.config_changed, self._reconcile)
        framework.observe(self.on.db_relation_changed, self._reconcile)
        framework.observe(self.on.db_relation_broken, self._reconcile)

    def _reconcile(self, event: ops.EventBase) -> None:
        """Converge workload configuration and unit status toward desired state."""
        container = self.unit.get_container("web")

        # 1. Ensure the Kubernetes Pebble sidecar container is reachable
        if not container.can_connect():
            self.unit.status = ops.WaitingStatus("Waiting for Pebble container")
            return

        # 2. Check if a database relation exists and provides a URI
        db_relation = self.model.get_relation("db")
        if not db_relation or not db_relation.app:
            self.unit.status = ops.BlockedStatus("Missing required 'db' relation")
            return

        db_uri = db_relation.data[db_relation.app].get("uri")
        if not db_uri:
            self.unit.status = ops.WaitingStatus("Waiting for database URI")
            return

        # 3. Validate configuration option
        port = self.config.get("port", 8080)
        if not isinstance(port, int) or port <= 0 or port > 65535:
            self.unit.status = ops.BlockedStatus(f"Invalid port configuration: {port}")
            return

        # 4. Push Pebble layer plan and replan service idempotently
        layer = {
            "summary": "demo-web-app layer",
            "description": "pebble config layer for demo-web-app",
            "services": {
                "web": {
                    "override": "replace",
                    "summary": "web server",
                    "command": f"/usr/local/bin/server --port={port}",
                    "startup": "enabled",
                    "environment": {"DATABASE_URL": db_uri},
                }
            },
        }
        container.add_layer("web", layer, combine=True)
        container.replan()

        logger.info("Reconciled web service on port %s after event %s", port, type(event).__name__)
        self.unit.status = ops.ActiveStatus(f"Running on port {port}")


if __name__ == "__main__":
    ops.main(DemoWebAppCharm)
