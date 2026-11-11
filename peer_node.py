import argparse
import os
import socket
import threading
import time

from common import (
    DEFAULT_PORT,
    recv_json,
    send_json,
    list_shared_files,
)


class PeerNode:
    def __init__(
        self,
        username,
        password,
        shared_dir,
        central_host,
        central_port,
        peer_host,
        peer_port,
    ):
        self.username = username
        self.password = password
        self.shared_dir = shared_dir
        self.central_host = central_host
        self.central_port = central_port
        self.peer_host = peer_host
        self.peer_port = peer_port

        os.makedirs(self.shared_dir, exist_ok=True)

    def central_request(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.central_host, self.central_port))
            send_json(sock, data)
            return recv_json(sock)

    def register(self):
        return self.central_request({
            "cmd": "REGISTER",
            "username": self.username,
            "password": self.password,
        })

    def login(self):
        return self.central_request({
            "cmd": "LOGIN",
            "username": self.username,
            "password": self.password,
            "peer_host": self.peer_host,
            "peer_port": self.peer_port,
        })

    def publish_files(self):
        files = list_shared_files(self.shared_dir)

        clean_files = []

        for file_info in files:
            clean_files.append({
                "name": file_info["name"],
                "description": file_info["description"],
                "relative_path": file_info["relative_path"],
                "size": file_info["size"],
            })

        return self.central_request({
            "cmd": "UPLOAD_FILES",
            "username": self.username,
            "files": clean_files,
        })

    def search(self, query):
        return self.central_request({
            "cmd": "SEARCH",
            "query": query,
        })

    def ping(self):
        return self.central_request({
            "cmd": "PING",
            "username": self.username,
        })

    def start_file_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.peer_host, self.peer_port))
        server.listen(10)

        print(
            f"Peer démarré sur "
            f"{self.peer_host}:{self.peer_port}"
        )

        while True:
            client, address = server.accept()

            threading.Thread(
                target=self.send_file,
                args=(client, address),
                daemon=True,
            ).start()

    def send_file(self, client, address):
        try:
            request = recv_json(client)

            if request.get("cmd") != "GET_FILE":
                send_json(client, {
                    "status": "ERROR",
                    "message": "Commande invalide",
                })
                return

            filename = os.path.basename(request.get("filename", ""))
            path = os.path.join(self.shared_dir, filename)

            if not os.path.isfile(path):
                send_json(client, {
                    "status": "ERROR",
                    "message": "Fichier introuvable",
                })
                return

            size = os.path.getsize(path)

            send_json(client, {
                "status": "OK",
                "filename": filename,
                "size": size,
            })

            with open(path, "rb") as file:
                while True:
                    data = file.read(65536)

                    if not data:
                        break

                    client.sendall(data)

        except Exception as error:
            print(f"Erreur peer {address}: {error}")

        finally:
            client.close()

    def start(self):
        threading.Thread(
            target=self.start_file_server,
            daemon=True,
        ).start()

        time.sleep(0.5)

        login_result = self.login()
        print("Connexion :", login_result)

        if login_result.get("status") != "OK":
            return

        publish_result = self.publish_files()
        print("Publication :", publish_result)

        while True:
            time.sleep(30)
            self.ping()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--shared-dir", default="shared")
    parser.add_argument("--central-host", default="127.0.0.1")
    parser.add_argument("--central-port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--peer-host", default="127.0.0.1")
    parser.add_argument("--peer-port", type=int, default=6001)

    parser.add_argument("--register", action="store_true")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--search")

    args = parser.parse_args()

    peer = PeerNode(
        username=args.username,
        password=args.password,
        shared_dir=args.shared_dir,
        central_host=args.central_host,
        central_port=args.central_port,
        peer_host=args.peer_host,
        peer_port=args.peer_port,
    )

    if args.register:
        print("Inscription :", peer.register())
        return

    if args.search:
        print("Recherche :", peer.search(args.search))
        return

    if args.login:
        peer.start()
        return

    parser.print_help()


if __name__ == "__main__":
    main()