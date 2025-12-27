#!/usr/bin/env python3
"""
Blueprint tests for pycolonies.
Tests blueprint definitions and blueprint instance CRUD operations.
"""

import unittest
import sys
import os
import time
import random
import string

# Prioritize local source over installed package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto import Crypto
from pycolonies import Colonies


class TestBlueprints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = os.environ.get('COLONIES_SERVER_HOST', 'localhost')
        cls.port = int(os.environ.get('COLONIES_SERVER_PORT', '50080'))
        cls.tls = os.environ.get('COLONIES_TLS', 'false').lower() == 'true'
        cls.colony_name = os.environ.get('COLONIES_COLONY_NAME', 'test')
        cls.executor_prvkey = os.environ.get('COLONIES_PRVKEY',
            'ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05')
        cls.colony_prvkey = os.environ.get('COLONIES_COLONY_PRVKEY',
            'ba949fa134981372d6da62b6a56f336ab4d843b22c02a4257dcf7d0d73097514')

        cls.client = Colonies(cls.host, cls.port, tls=cls.tls, native_crypto=False)

        # Skip tests if server is not available
        try:
            server_prvkey = os.environ.get('COLONIES_SERVER_PRVKEY',
                'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d')
            cls.client.list_colonies(server_prvkey)
        except Exception:
            raise unittest.SkipTest("Colonies server not available")

    def _random_suffix(self):
        """Generate random suffix for unique names."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def test_blueprint_definition_crud(self):
        """Test blueprint definition create, read, list, delete operations."""
        suffix = self._random_suffix()
        def_name = f"test-def-{suffix}"
        kind = f"TestKind-{suffix}"

        # Create blueprint definition (requires colony owner key)
        definition = {
            "kind": kind,
            "metadata": {
                "name": def_name,
                "colonyname": self.colony_name
            },
            "spec": {
                "names": {
                    "kind": kind
                }
            }
        }

        result = self.client.add_blueprint_definition(definition, self.colony_prvkey)
        self.assertIsNotNone(result)

        # Get the blueprint definition
        retrieved = self.client.get_blueprint_definition(self.colony_name, def_name, self.colony_prvkey)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['kind'], kind)

        # List blueprint definitions
        definitions = self.client.get_blueprint_definitions(self.colony_name, self.colony_prvkey)
        self.assertTrue(definitions is None or isinstance(definitions, list))
        if definitions:
            found = any(d.get('metadata', {}).get('name') == def_name for d in definitions)
            self.assertTrue(found)

        # Remove blueprint definition
        self.client.remove_blueprint_definition(self.colony_name, def_name, self.colony_prvkey)

        # Verify it's gone
        with self.assertRaises(Exception):
            self.client.get_blueprint_definition(self.colony_name, def_name, self.colony_prvkey)

    def test_blueprint_instance_crud(self):
        """Test blueprint instance create, read, update, delete operations."""
        suffix = self._random_suffix()
        def_name = f"test-def-{suffix}"
        bp_name = f"test-bp-{suffix}"
        kind = f"TestKind-{suffix}"

        # First create a blueprint definition
        definition = {
            "kind": kind,
            "metadata": {
                "name": def_name,
                "colonyname": self.colony_name
            },
            "spec": {
                "names": {
                    "kind": kind
                }
            }
        }
        self.client.add_blueprint_definition(definition, self.colony_prvkey)

        try:
            # Create blueprint instance (executor key)
            blueprint = {
                "kind": kind,
                "metadata": {
                    "name": bp_name,
                    "colonyname": self.colony_name
                },
                "handler": {
                    "executortype": "test-reconciler"
                },
                "spec": {
                    "deviceType": "light",
                    "power": False,
                    "brightness": 0
                }
            }

            result = self.client.add_blueprint(blueprint, self.executor_prvkey)
            self.assertIsNotNone(result)

            # Get the blueprint
            retrieved = self.client.get_blueprint(self.colony_name, bp_name, self.executor_prvkey)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved['kind'], kind)
            self.assertEqual(retrieved['spec']['power'], False)

            # List blueprints
            blueprints = self.client.get_blueprints(self.colony_name, self.executor_prvkey)
            self.assertTrue(blueprints is None or isinstance(blueprints, list))
            if blueprints:
                found = any(b.get('metadata', {}).get('name') == bp_name for b in blueprints)
                self.assertTrue(found)

            # Update blueprint
            blueprint['spec']['power'] = True
            blueprint['spec']['brightness'] = 100
            self.client.update_blueprint(blueprint, self.executor_prvkey)

            # Verify update
            updated = self.client.get_blueprint(self.colony_name, bp_name, self.executor_prvkey)
            self.assertEqual(updated['spec']['power'], True)
            self.assertEqual(updated['spec']['brightness'], 100)

            # Remove blueprint
            self.client.remove_blueprint(self.colony_name, bp_name, self.executor_prvkey)

            # Verify it's gone
            with self.assertRaises(Exception):
                self.client.get_blueprint(self.colony_name, bp_name, self.executor_prvkey)

        finally:
            # Clean up definition
            try:
                self.client.remove_blueprint_definition(self.colony_name, def_name, self.colony_prvkey)
            except:
                pass

    def test_blueprint_status_update(self):
        """Test updating blueprint status (current state)."""
        suffix = self._random_suffix()
        def_name = f"test-def-{suffix}"
        bp_name = f"test-bp-{suffix}"
        kind = f"TestKind-{suffix}"

        # Create definition
        definition = {
            "kind": kind,
            "metadata": {
                "name": def_name,
                "colonyname": self.colony_name
            },
            "spec": {
                "names": {
                    "kind": kind
                }
            }
        }
        self.client.add_blueprint_definition(definition, self.colony_prvkey)

        try:
            # Create blueprint instance
            blueprint = {
                "kind": kind,
                "metadata": {
                    "name": bp_name,
                    "colonyname": self.colony_name
                },
                "handler": {
                    "executortype": "test-reconciler"
                },
                "spec": {
                    "power": True,
                    "brightness": 80
                }
            }
            self.client.add_blueprint(blueprint, self.executor_prvkey)

            # Update status
            status = {
                "power": True,
                "brightness": 80,
                "lastSeen": "2024-01-01T12:00:00Z"
            }
            self.client.update_blueprint_status(self.colony_name, bp_name, status, self.executor_prvkey)

            # Verify status was updated
            retrieved = self.client.get_blueprint(self.colony_name, bp_name, self.executor_prvkey)
            self.assertIsNotNone(retrieved.get('status'))
            self.assertEqual(retrieved['status']['power'], True)
            self.assertEqual(retrieved['status']['brightness'], 80)

        finally:
            # Clean up
            try:
                self.client.remove_blueprint(self.colony_name, bp_name, self.executor_prvkey)
            except:
                pass
            try:
                self.client.remove_blueprint_definition(self.colony_name, def_name, self.colony_prvkey)
            except:
                pass

    def test_blueprint_filter_by_kind(self):
        """Test filtering blueprints by kind."""
        suffix = self._random_suffix()
        def_name = f"test-def-{suffix}"
        bp_name = f"test-bp-{suffix}"
        kind = f"FilterKind-{suffix}"

        # Create definition
        definition = {
            "kind": kind,
            "metadata": {
                "name": def_name,
                "colonyname": self.colony_name
            },
            "spec": {
                "names": {
                    "kind": kind
                }
            }
        }
        self.client.add_blueprint_definition(definition, self.colony_prvkey)

        try:
            # Create blueprint instance
            blueprint = {
                "kind": kind,
                "metadata": {
                    "name": bp_name,
                    "colonyname": self.colony_name
                },
                "handler": {
                    "executortype": "test-reconciler"
                },
                "spec": {
                    "test": True
                }
            }
            self.client.add_blueprint(blueprint, self.executor_prvkey)

            # Filter by kind
            blueprints = self.client.get_blueprints(self.colony_name, self.executor_prvkey, kind=kind)
            self.assertTrue(blueprints is None or isinstance(blueprints, list))
            if blueprints:
                for bp in blueprints:
                    self.assertEqual(bp['kind'], kind)

        finally:
            # Clean up
            try:
                self.client.remove_blueprint(self.colony_name, bp_name, self.executor_prvkey)
            except:
                pass
            try:
                self.client.remove_blueprint_definition(self.colony_name, def_name, self.colony_prvkey)
            except:
                pass


if __name__ == '__main__':
    unittest.main()
