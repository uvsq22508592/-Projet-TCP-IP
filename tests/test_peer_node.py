import os
import socket
import tempfile
import threading
import unittest

from common import recv_exact, recv_json, send_json
from peer_node import PeerNode


class PeerNodeTests(unittest.TestCase):
    def test_selected_file_can_be_downloaded_without_exposing_siblings(self):
        with tempfile.TemporaryDirectory() as shared_dir:
            shared_file = os.path.join(shared_dir, "shared.txt")
            private_file = os.path.join(shared_dir, "private.txt")
            with open(shared_file, "wb") as file:
                file.write(b"shared data")
            with open(private_file, "wb") as file:
                file.write(b"private data")

            peer = PeerNode(
                username="alice",
                password="secret",
                shared_dir=shared_file,
                central_host="127.0.0.1",
                central_port=5000,
                peer_host="127.0.0.1",
                peer_port=6001,
            )

            client, server = socket.socketpair()
            worker = threading.Thread(
                target=peer.send_file,
                args=(server, ("local", 0)),
            )
            worker.start()
            try:
                send_json(client, {
                    "cmd": "GET_FILE",
                    "filename": "shared.txt",
                })
                response = recv_json(client)
                self.assertEqual(response["status"], "OK")
                self.assertEqual(
                    recv_exact(client, response["size"]),
                    b"shared data",
                )
            finally:
                client.close()
                worker.join(timeout=2)

            client, server = socket.socketpair()
            worker = threading.Thread(
                target=peer.send_file,
                args=(server, ("local", 0)),
            )
            worker.start()
            try:
                send_json(client, {
                    "cmd": "GET_FILE",
                    "filename": "private.txt",
                })
                response = recv_json(client)
                self.assertEqual(response["status"], "ERROR")
            finally:
                client.close()
                worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
