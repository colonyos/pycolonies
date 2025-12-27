#!/usr/bin/env python3
"""
Channel test with executor/client chat via WebSocket.
Tests bidirectional communication between a client (process submitter) and an executor.
"""

import unittest
import sys
import os
import threading
import time

# Prioritize local source over installed package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto import Crypto
from pycolonies import Colonies, func_spec


class TestChannels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = os.environ.get('COLONIES_SERVER_HOST', 'localhost')
        cls.port = int(os.environ.get('COLONIES_SERVER_PORT', '50080'))
        cls.tls = os.environ.get('COLONIES_TLS', 'false').lower() == 'true'
        cls.colony_name = os.environ.get('COLONIES_COLONY_NAME', 'test')
        cls.executor_prvkey = os.environ.get('COLONIES_PRVKEY',
            'ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05')
        cls.executor_type = os.environ.get('COLONIES_EXECUTOR_TYPE', 'cli')

        cls.client = Colonies(cls.host, cls.port, tls=cls.tls, native_crypto=False)

        # Skip tests if server is not available
        try:
            server_prvkey = os.environ.get('COLONIES_SERVER_PRVKEY',
                'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d')
            cls.client.list_colonies(server_prvkey)
        except Exception:
            raise unittest.SkipTest("Colonies server not available")

    def test_channel_append_and_read(self):
        """Test basic channel append and read operations."""
        # Submit a process with a channel
        spec = func_spec(
            "echo",
            ["hello"],
            self.colony_name,
            self.executor_type,
            maxexectime=60,
            maxwaittime=60,
            maxretries=0
        )
        spec.channels = ["chat"]

        process = self.client.submit_func_spec(spec, self.executor_prvkey)
        self.assertIsNotNone(process.processid)

        # Assign the process (as executor)
        assigned = self.client.assign(self.colony_name, 10, self.executor_prvkey)
        self.assertEqual(assigned.processid, process.processid)

        # Wait for channel to be ready after assignment
        time.sleep(0.2)

        # Client appends a message to the channel
        self.client.channel_append(
            process.processid,
            "chat",
            1,  # sequence
            "Hello from client!",
            self.executor_prvkey
        )

        # Executor reads the message
        entries = self.client.channel_read(
            process.processid,
            "chat",
            0,  # after_seq
            10,  # limit
            self.executor_prvkey
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['payload'], b"Hello from client!")
        self.assertEqual(entries[0]['sequence'], 1)

        # Executor responds
        self.client.channel_append(
            process.processid,
            "chat",
            2,  # sequence
            "Hello from executor!",
            self.executor_prvkey,
            in_reply_to=1
        )

        # Client reads all messages
        all_entries = self.client.channel_read(
            process.processid,
            "chat",
            0,
            10,
            self.executor_prvkey
        )

        self.assertEqual(len(all_entries), 2)
        self.assertEqual(all_entries[1]['payload'], b"Hello from executor!")
        self.assertEqual(all_entries[1]['inreplyto'], 1)

        # Close the process
        self.client.close(process.processid, ["done"], self.executor_prvkey)

    def test_channel_with_end_message(self):
        """Test channel with end-of-stream message type."""
        # Submit a process with a channel
        spec = func_spec(
            "stream",
            [],
            self.colony_name,
            self.executor_type,
            maxexectime=60,
            maxwaittime=60,
            maxretries=0
        )
        spec.channels = ["stream"]

        process = self.client.submit_func_spec(spec, self.executor_prvkey)
        assigned = self.client.assign(self.colony_name, 10, self.executor_prvkey)
        time.sleep(0.2)  # Wait for channel to be ready

        # Send multiple data messages followed by end
        for i in range(1, 4):
            self.client.channel_append(
                process.processid,
                "stream",
                i,
                f"chunk {i}",
                self.executor_prvkey,
                payload_type="data"
            )

        # Send end-of-stream marker
        self.client.channel_append(
            process.processid,
            "stream",
            4,
            "",
            self.executor_prvkey,
            payload_type="end"
        )

        # Read all messages
        entries = self.client.channel_read(
            process.processid,
            "stream",
            0,
            10,
            self.executor_prvkey
        )

        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0]['type'], 'data')
        self.assertEqual(entries[3]['type'], 'end')

        self.client.close(process.processid, ["done"], self.executor_prvkey)

    def test_channel_websocket_subscription(self):
        """Test WebSocket channel subscription for real-time messages."""
        # Submit a process with a channel
        spec = func_spec(
            "realtime",
            [],
            self.colony_name,
            self.executor_type,
            maxexectime=60,
            maxwaittime=60,
            maxretries=0
        )
        spec.channels = ["realtime"]

        process = self.client.submit_func_spec(spec, self.executor_prvkey)
        assigned = self.client.assign(self.colony_name, 10, self.executor_prvkey)
        time.sleep(0.2)  # Wait for channel to be ready

        received_messages = []

        def sender_thread():
            """Simulates executor sending messages."""
            time.sleep(0.5)  # Wait for subscriber to connect
            sender = Colonies(self.host, self.port, tls=self.tls, native_crypto=False)
            for i in range(1, 4):
                sender.channel_append(
                    process.processid,
                    "realtime",
                    i,
                    f"realtime message {i}",
                    self.executor_prvkey
                )
                time.sleep(0.1)

        # Start sender in background thread
        sender = threading.Thread(target=sender_thread)
        sender.start()

        # Subscribe and collect messages
        def on_message(entries):
            for entry in entries:
                received_messages.append(entry)
            return len(received_messages) < 3

        self.client.subscribe_channel(
            process.processid,
            "realtime",
            self.executor_prvkey,
            timeout=5,
            callback=on_message
        )

        sender.join()

        self.assertEqual(len(received_messages), 3)
        self.assertEqual(received_messages[0]['payload'], b"realtime message 1")
        self.assertEqual(received_messages[2]['payload'], b"realtime message 3")

        self.client.close(process.processid, ["done"], self.executor_prvkey)

    def test_channel_chat_simulation(self):
        """Simulate a chat between client and executor using channels."""
        # Submit a process with a channel
        spec = func_spec(
            "chat",
            [],
            self.colony_name,
            self.executor_type,
            maxexectime=60,
            maxwaittime=60,
            maxretries=0
        )
        spec.channels = ["chat"]

        process = self.client.submit_func_spec(spec, self.executor_prvkey)
        assigned = self.client.assign(self.colony_name, 10, self.executor_prvkey)
        time.sleep(0.2)  # Wait for channel to be ready

        executor_received = []
        client_received = []

        def executor_thread():
            """Executor subscribes and responds to messages."""
            time.sleep(0.1)
            executor = Colonies(self.host, self.port, tls=self.tls, native_crypto=False)

            def on_executor_message(entries):
                for entry in entries:
                    executor_received.append(entry)
                    # Respond to the message
                    response_seq = entry['sequence'] + 100
                    executor.channel_append(
                        process.processid,
                        "chat",
                        response_seq,
                        f"Executor received: {entry['payload'].decode()}",
                        self.executor_prvkey,
                        in_reply_to=entry['sequence']
                    )
                return len(executor_received) < 2

            executor.subscribe_channel(
                process.processid,
                "chat",
                self.executor_prvkey,
                timeout=5,
                callback=on_executor_message
            )

        def client_thread():
            """Client subscribes for executor responses."""
            time.sleep(0.3)
            client = Colonies(self.host, self.port, tls=self.tls, native_crypto=False)

            def on_client_message(entries):
                for entry in entries:
                    # Only collect executor responses (high sequence numbers)
                    if entry['sequence'] >= 100:
                        client_received.append(entry)
                return len(client_received) < 2

            client.subscribe_channel(
                process.processid,
                "chat",
                self.executor_prvkey,
                timeout=5,
                callback=on_client_message
            )

        # Start executor and client subscribers
        executor = threading.Thread(target=executor_thread)
        client = threading.Thread(target=client_thread)
        executor.start()
        client.start()

        # Send messages from "client" side
        time.sleep(0.5)
        self.client.channel_append(
            process.processid,
            "chat",
            1,
            "Hello executor!",
            self.executor_prvkey
        )
        time.sleep(0.2)
        self.client.channel_append(
            process.processid,
            "chat",
            2,
            "How are you?",
            self.executor_prvkey
        )

        executor.join(timeout=6)
        client.join(timeout=6)

        # Verify executor received client messages
        self.assertGreaterEqual(len(executor_received), 2)
        self.assertEqual(executor_received[0]['payload'], b"Hello executor!")

        # Verify client received executor responses
        self.assertGreaterEqual(len(client_received), 2)
        self.assertIn(b"Executor received:", client_received[0]['payload'])

        self.client.close(process.processid, ["done"], self.executor_prvkey)


if __name__ == '__main__':
    unittest.main()
