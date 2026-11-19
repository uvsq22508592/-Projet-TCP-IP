import unittest

from server_central import CentralServer


class CentralServerTests(unittest.TestCase):
    def setUp(self):
        self.server = CentralServer()

    def test_register_login_publish_and_search(self):
        self.assertEqual(
            self.server.register("alice", "secret")["status"],
            "OK",
        )
        self.assertEqual(
            self.server.login("alice", "secret", "127.0.0.1", 6001)["status"],
            "OK",
        )
        self.assertEqual(
            self.server.upload_files(
                "alice",
                [{
                    "name": "song.mp3",
                    "description": "jazz music",
                }],
            )["status"],
            "OK",
        )

        result = self.server.search("JAZZ")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["results"][0]["filename"], "song.mp3")
        self.assertEqual(
            result["results"][0]["relative_path"],
            "song.mp3",
        )
        self.assertEqual(result["results"][0]["peer_port"], 6001)

    def test_duplicate_registration_and_invalid_login(self):
        self.assertEqual(
            self.server.register("alice", "secret")["status"],
            "OK",
        )
        self.assertEqual(
            self.server.register("alice", "other")["status"],
            "ERROR",
        )
        self.assertEqual(
            self.server.login("alice", "wrong", "127.0.0.1", 6001)["status"],
            "ERROR",
        )

    def test_logout_removes_published_files(self):
        self.server.register("alice", "secret")
        self.server.login("alice", "secret", "127.0.0.1", 6001)
        self.server.upload_files(
            "alice",
            [{"name": "document.pdf", "description": "document"}],
        )

        self.assertEqual(self.server.logout("alice")["status"], "OK")
        self.assertEqual(self.server.search("document")["results"], [])

    def test_list_all_published_files_from_multiple_peers(self):
        self.server.register("alice", "secret")
        self.server.register("bob", "secret")
        self.server.login("alice", "secret", "127.0.0.1", 6001)
        self.server.login("bob", "secret", "127.0.0.2", 6002)
        self.server.upload_files(
            "alice",
            [
                {"name": "photo.jpg", "relative_path": "images/photo.jpg"},
                {"name": "music.mp3", "relative_path": "audio/music.mp3"},
            ],
        )
        self.server.upload_files(
            "bob",
            [{"name": "report.pdf", "relative_path": "docs/report.pdf"}],
        )

        result = self.server.list_files()
        self.assertEqual(result["status"], "OK")
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(
            {item["relative_path"] for item in result["results"]},
            {"images/photo.jpg", "audio/music.mp3", "docs/report.pdf"},
        )


if __name__ == "__main__":
    unittest.main()
