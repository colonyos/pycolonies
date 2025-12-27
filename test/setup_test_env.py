#!/usr/bin/env python3
"""
Setup script for test environment.
Creates test colony and executor using the Python client.
Similar approach to colonies-ts integration tests.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pycolonies import Colonies
from crypto import Crypto

# Test configuration - matches GitHub Actions workflow
TEST_CONFIG = {
    'host': os.environ.get('COLONIES_SERVER_HOST', 'localhost'),
    'port': int(os.environ.get('COLONIES_SERVER_PORT', '50080')),
    'tls': os.environ.get('COLONIES_TLS', 'false').lower() == 'true',

    # Server private key - for server admin operations
    'server_prvkey': os.environ.get('COLONIES_SERVER_PRVKEY',
        'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d'),

    # Colony configuration
    'colony_name': os.environ.get('COLONIES_COLONY_NAME', 'test'),
    'colony_id': os.environ.get('COLONIES_COLONY_ID',
        '4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4'),
    'colony_prvkey': os.environ.get('COLONIES_COLONY_PRVKEY',
        'ba949fa134981372d6da62b6a56f336ab4d843b22c02a4257dcf7d0d73097514'),

    # Executor configuration
    'executor_id': os.environ.get('COLONIES_EXECUTOR_ID',
        '3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac'),
    'executor_prvkey': os.environ.get('COLONIES_PRVKEY',
        'ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05'),
    'executor_name': os.environ.get('COLONIES_EXECUTOR_NAME', 'test-executor'),
    'executor_type': os.environ.get('COLONIES_EXECUTOR_TYPE', 'cli'),
}


def setup_test_environment():
    """Set up test colony and executor."""
    print(f"Setting up test environment:")
    print(f"  Host: {TEST_CONFIG['host']}")
    print(f"  Port: {TEST_CONFIG['port']}")
    print(f"  TLS:  {TEST_CONFIG['tls']}")

    client = Colonies(
        TEST_CONFIG['host'],
        TEST_CONFIG['port'],
        tls=TEST_CONFIG['tls'],
        native_crypto=False
    )

    # Check if colony exists
    try:
        colonies = client.list_colonies(TEST_CONFIG['server_prvkey'])
        colony_exists = any(c['name'] == TEST_CONFIG['colony_name'] for c in colonies)
    except Exception as e:
        print(f"Could not list colonies: {e}")
        colony_exists = False

    # Create colony if needed
    if not colony_exists:
        try:
            colony = {
                'colonyid': TEST_CONFIG['colony_id'],
                'name': TEST_CONFIG['colony_name']
            }
            client.add_colony(colony, TEST_CONFIG['server_prvkey'])
            print(f"Created colony: {TEST_CONFIG['colony_name']}")
        except Exception as e:
            print(f"Could not create colony (may already exist): {e}")
    else:
        print(f"Colony already exists: {TEST_CONFIG['colony_name']}")

    # Add executor
    try:
        executor = {
            'executorid': TEST_CONFIG['executor_id'],
            'executorname': TEST_CONFIG['executor_name'],
            'executortype': TEST_CONFIG['executor_type'],
            'colonyname': TEST_CONFIG['colony_name'],
        }
        client.add_executor(executor, TEST_CONFIG['colony_prvkey'])
        print(f"Added executor: {TEST_CONFIG['executor_name']}")
    except Exception as e:
        print(f"Could not add executor (may already exist): {e}")

    # Approve executor
    try:
        client.approve_executor(
            TEST_CONFIG['colony_name'],
            TEST_CONFIG['executor_name'],
            TEST_CONFIG['colony_prvkey']
        )
        print(f"Approved executor: {TEST_CONFIG['executor_name']}")
    except Exception as e:
        print(f"Could not approve executor (may already be approved): {e}")

    print("Test environment setup complete!")
    return True


if __name__ == '__main__':
    try:
        setup_test_environment()
        sys.exit(0)
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)
