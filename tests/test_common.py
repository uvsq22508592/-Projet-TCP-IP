import os
import socket
import tempfile
import unittest

from common import (
    keywords_from_text,
    list_shared_files,
    recv_json,
    send_json,
    sha256_password,
)


class CommonTests(unittest.TestCase):
    def test_json_transport_and_password_hashing(self):
        left, right = socket.socketpair()
        try:
            send_json(left, {"status": "OK", "message": "réussi"})
            self.assertEqual(
                recv_json(right),
                {"status": "OK", "message": "réussi"},
            )
        finally:
            left.close()
            right.close()

        self.assertNotEqual(sha256_password("secret"), "secret")
        self.assertEqual(keywords_from_text("Musique JAZZ"), ["musique", "jazz"])

    def test_list_shared_files_returns_relative_metadata(self):
        with tempfile.TemporaryDirectory() as shared_dir:
            nested_dir = os.path.join(shared_dir, "albums")
            os.makedirs(nested_dir)
            path = os.path.join(nested_dir, "song.mp3")
            with open(path, "wb") as file:
                file.write(b"audio")

            files = list_shared_files(shared_dir)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["name"], "song.mp3")
        self.assertEqual(files[0]["relative_path"], os.path.join("albums", "song.mp3"))
        self.assertEqual(files[0]["size"], 5)


if __name__ == "__main__":
    unittest.main()
