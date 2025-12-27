#!/usr/bin/env python3
"""
API tests for pycolonies.
Tests additional API methods: generators, users, process graphs, file labels, etc.
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
from pycolonies import Colonies, func_spec


class TestAPIEndpoints(unittest.TestCase):
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
        cls.server_prvkey = os.environ.get('COLONIES_SERVER_PRVKEY',
            'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d')

        cls.client = Colonies(cls.host, cls.port, tls=cls.tls, native_crypto=False)

        # Skip tests if server is not available
        try:
            cls.client.list_colonies(cls.server_prvkey)
        except Exception:
            raise unittest.SkipTest("Colonies server not available")

    def _random_suffix(self):
        """Generate random suffix for unique names."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def test_get_executor(self):
        """Test getting a specific executor."""
        # First list executors to find one
        executors = self.client.list_executors(self.colony_name, self.executor_prvkey)

        if executors and len(executors) > 0:
            executor_name = executors[0].get('executorname')
            if executor_name:
                executor = self.client.get_executor(self.colony_name, executor_name, self.executor_prvkey)
                self.assertIsNotNone(executor)
                self.assertEqual(executor.get('executorname'), executor_name)

    def test_get_users(self):
        """Test getting users in a colony."""
        try:
            users = self.client.get_users(self.colony_name, self.server_prvkey)
            # Users might be None or empty list
            self.assertTrue(users is None or isinstance(users, list))
        except Exception as e:
            # User operations may require special permissions
            if "Access denied" in str(e):
                self.skipTest("User operations require admin permissions")

    def test_user_crud(self):
        """Test user create, read, delete operations."""
        crypto = Crypto()
        user_prvkey = crypto.prvkey()
        user_id = crypto.id(user_prvkey)
        user_name = f"test-user-{self._random_suffix()}"

        user = {
            "colonyname": self.colony_name,
            "userid": user_id,
            "name": user_name,
            "email": "test@example.com",
            "phone": ""
        }

        # Add user (requires server/admin key)
        try:
            result = self.client.add_user(user, self.server_prvkey)
            self.assertIsNotNone(result)

            # Get users and verify
            users = self.client.get_users(self.colony_name, self.server_prvkey)
            if users:
                found = any(u.get('name') == user_name for u in users)
                self.assertTrue(found)

            # Remove user
            self.client.remove_user(self.colony_name, user_name, self.server_prvkey)
        except Exception as e:
            # User operations may require special permissions
            if "Access denied" in str(e):
                self.skipTest("User operations require admin permissions")
            # Clean up on failure
            try:
                self.client.remove_user(self.colony_name, user_name, self.server_prvkey)
            except:
                pass
            raise e

    def test_get_generators(self):
        """Test getting generators in a colony."""
        generators = self.client.get_generators(self.colony_name, self.executor_prvkey)
        # Generators might be None or empty list
        self.assertTrue(generators is None or isinstance(generators, list))

    def test_get_processgraphs(self):
        """Test getting process graphs (workflows)."""
        graphs = self.client.get_processgraphs(self.colony_name, 10, self.executor_prvkey)
        # Process graphs might be None or empty list
        self.assertTrue(graphs is None or isinstance(graphs, list))

    def test_get_file_labels(self):
        """Test getting file labels."""
        labels = self.client.get_file_labels(self.colony_name, self.executor_prvkey)
        # Labels might be None or empty list
        self.assertTrue(labels is None or isinstance(labels, list))

    def test_process_lifecycle(self):
        """Test process submit, list, remove operations."""
        # Submit a process
        spec = func_spec(
            "test_func",
            ["arg1"],
            self.colony_name,
            "cli",
            maxexectime=60,
            maxwaittime=60,
            maxretries=0
        )

        process = self.client.submit_func_spec(spec, self.executor_prvkey)
        self.assertIsNotNone(process.processid)

        try:
            # List waiting processes (state 0 = waiting)
            processes = self.client.list_processes(self.colony_name, 10, 0, self.executor_prvkey)
            self.assertTrue(processes is None or isinstance(processes, list))

            # Remove the process
            self.client.remove_process(process.processid, self.executor_prvkey)
        except Exception as e:
            # Clean up on failure
            try:
                self.client.remove_process(process.processid, self.executor_prvkey)
            except:
                pass
            raise e

    def test_stats(self):
        """Test getting colony statistics."""
        stats = self.client.stats(self.colony_name, self.executor_prvkey)
        self.assertIsNotNone(stats)

    def test_get_functions(self):
        """Test getting functions by colony."""
        functions = self.client.get_functions_by_colony(self.colony_name, self.executor_prvkey)
        self.assertTrue(functions is None or isinstance(functions, list))


class TestCronOperations(unittest.TestCase):
    """Test cron-related operations."""

    @classmethod
    def setUpClass(cls):
        cls.host = os.environ.get('COLONIES_SERVER_HOST', 'localhost')
        cls.port = int(os.environ.get('COLONIES_SERVER_PORT', '50080'))
        cls.tls = os.environ.get('COLONIES_TLS', 'false').lower() == 'true'
        cls.colony_name = os.environ.get('COLONIES_COLONY_NAME', 'test')
        cls.executor_prvkey = os.environ.get('COLONIES_PRVKEY',
            'ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05')

        cls.client = Colonies(cls.host, cls.port, tls=cls.tls, native_crypto=False)

        # Skip tests if server is not available
        try:
            server_prvkey = os.environ.get('COLONIES_SERVER_PRVKEY',
                'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d')
            cls.client.list_colonies(server_prvkey)
        except Exception:
            raise unittest.SkipTest("Colonies server not available")

    def test_get_crons(self):
        """Test getting crons in a colony."""
        crons = self.client.get_crons(self.colony_name, 10, self.executor_prvkey)
        self.assertTrue(crons is None or isinstance(crons, list))


class TestAttributeOperations(unittest.TestCase):
    """Test attribute operations on processes."""

    @classmethod
    def setUpClass(cls):
        cls.host = os.environ.get('COLONIES_SERVER_HOST', 'localhost')
        cls.port = int(os.environ.get('COLONIES_SERVER_PORT', '50080'))
        cls.tls = os.environ.get('COLONIES_TLS', 'false').lower() == 'true'
        cls.colony_name = os.environ.get('COLONIES_COLONY_NAME', 'test')
        cls.executor_prvkey = os.environ.get('COLONIES_PRVKEY',
            'ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05')

        cls.client = Colonies(cls.host, cls.port, tls=cls.tls, native_crypto=False)

        # Skip tests if server is not available
        try:
            server_prvkey = os.environ.get('COLONIES_SERVER_PRVKEY',
                'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d')
            cls.client.list_colonies(server_prvkey)
        except Exception:
            raise unittest.SkipTest("Colonies server not available")

    def test_attribute_on_process(self):
        """Test adding and getting attributes on a running process."""
        # Submit a process
        spec = func_spec(
            "attr_test",
            [],
            self.colony_name,
            "cli",
            maxexectime=60,
            maxwaittime=60,
            maxretries=0
        )

        process = self.client.submit_func_spec(spec, self.executor_prvkey)

        try:
            # Assign the process so it becomes running
            assigned = self.client.assign(self.colony_name, 10, self.executor_prvkey)
            self.assertEqual(assigned.processid, process.processid)

            # Add attribute to running process
            attr = self.client.add_attribute(
                process.processid,
                "test_key",
                "test_value",
                self.executor_prvkey
            )
            self.assertIsNotNone(attr)

            # Get attribute
            if attr and 'attributeid' in attr:
                retrieved = self.client.get_attribute(attr['attributeid'], self.executor_prvkey)
                self.assertIsNotNone(retrieved)
                self.assertEqual(retrieved.get('key'), 'test_key')
                self.assertEqual(retrieved.get('value'), 'test_value')

            # Close the process
            self.client.close(process.processid, ["done"], self.executor_prvkey)

        except Exception as e:
            # Clean up on failure
            try:
                self.client.close(process.processid, ["failed"], self.executor_prvkey)
            except:
                try:
                    self.client.remove_process(process.processid, self.executor_prvkey)
                except:
                    pass
            raise e


if __name__ == '__main__':
    unittest.main()
