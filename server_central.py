import argparse
import socket
import threading
import time
from collections import defaultdict

from common import (
    DEFAULT_PORT,
    keywords_from_text,
    recv_json,
    send_json,
    sha256_password,
)


class CentralServer:
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.users = {}
        self.peers = {}
        self.file_index = defaultdict(list)
        self.lock = threading.Lock()

    def register(self, username, password):
        if not username or not password:
            return {
                "status": "ERROR",
                "message": "Nom d'utilisateur ou mot de passe vide",
            }

        with self.lock:
            if username in self.users:
                return {
                    "status": "ERROR",
                    "message": "Utilisateur déjà enregistré",
                }

            self.users[username] = sha256_password(password)

        return {
            "status": "OK",
            "message": "Utilisateur enregistré",
        }

    def login(self, username, password, peer_host, peer_port):
        with self.lock:
            saved_password = self.users.get(username)

            if saved_password is None:
                return {
                    "status": "ERROR",
                    "message": "Utilisateur inconnu",
                }

            if saved_password != sha256_password(password):
                return {
                    "status": "ERROR",
                    "message": "Mot de passe incorrect",
                }

            self.peers[username] = {
                "host": peer_host,
                "port": int(peer_port),
                "last_seen": time.time(),
                "files": [],
            }

        return {
            "status": "OK",
            "message": "Connexion réussie",
        }

    def upload_files(self, username, files):
        with self.lock:
            peer = self.peers.get(username)

            if peer is None:
                return {
                    "status": "ERROR",
                    "message": "Utilisateur non connecté",
                }

            peer["files"] = files
            peer["last_seen"] = time.time()
            self.rebuild_index()

        return {
            "status": "OK",
            "message": f"{len(files)} fichier(s) publié(s)",
        }

    def rebuild_index(self):
        self.file_index.clear()

        for username, peer in self.peers.items():
            for file_info in peer["files"]:
                filename = file_info.get("name", "")
                description = file_info.get("description", "")

                entry = {
                    "username": username,
                    "filename": filename,
                    "description": description,
                    "peer_host": peer["host"],
                    "peer_port": peer["port"],
                }

                text = f"{filename} {description}"

                for keyword in keywords_from_text(text):
                    if entry not in self.file_index[keyword]:
                        self.file_index[keyword].append(entry)

    def search(self, query):
        keywords = keywords_from_text(query)

        if not keywords:
            return {
                "status": "ERROR",
                "message": "Recherche vide",
            }

        results = []
        already_found = set()

        with self.lock:
            for keyword in keywords:
                for file_info in self.file_index.get(keyword, []):
                    identifier = (
                        file_info["username"],
                        file_info["filename"],
                    )

                    if identifier not in already_found:
                        already_found.add(identifier)
                        results.append(file_info)

        return {
            "status": "OK",
            "results": results,
        }

    def ping(self, username):
        with self.lock:
            if username not in self.peers:
                return {
                    "status": "ERROR",
                    "message": "Utilisateur non connecté",
                }

            self.peers[username]["last_seen"] = time.time()

        return {
            "status": "OK",
            "message": "Heartbeat reçu",
        }

    def logout(self, username):
        with self.lock:
            self.peers.pop(username, None)
            self.rebuild_index()

        return {
            "status": "OK",
            "message": "Utilisateur déconnecté",
        }

    def remove_inactive_peers(self):
        with self.lock:
            now = time.time()
            inactive_users = [
                username
                for username, peer in self.peers.items()
                if now - peer["last_seen"] > 90
            ]

            for username in inactive_users:
                del self.peers[username]

            if inactive_users:
                self.rebuild_index()

    def process_request(self, request, client_address):
        command = request.get("cmd")

        if command == "REGISTER":
            return self.register(
                request.get("username"),
                request.get("password"),
            )

        if command == "LOGIN":
            return self.login(
                request.get("username"),
                request.get("password"),
                request.get("peer_host", client_address[0]),
                request.get("peer_port", 0),
            )

        if command == "UPLOAD_FILES":
            return self.upload_files(
                request.get("username"),
                request.get("files", []),
            )

        if command == "SEARCH":
            return self.search(request.get("query", ""))

        if command == "PING":
            return self.ping(request.get("username"))

        if command == "LOGOUT":
            return self.logout(request.get("username"))

        return {
            "status": "ERROR",
            "message": "Commande inconnue",
        }

    def handle_client(self, client_socket, client_address):
        try:
            while True:
                request = recv_json(client_socket)

                if request is None:
                    break

                response = self.process_request(
                    request,
                    client_address,
                )

                send_json(client_socket, response)

        except Exception as error:
            try:
                send_json(
                    client_socket,
                    {
                        "status": "ERROR",
                        "message": str(error),
                    },
                )
            except Exception:
                pass

        finally:
            client_socket.close()

    def cleanup_loop(self):
        while True:
            time.sleep(30)
            self.remove_inactive_peers()

    def start(self):
        server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        server_socket.bind((self.host, self.port))
        server_socket.listen(20)

        threading.Thread(
            target=self.cleanup_loop,
            daemon=True,
        ).start()

        print(
            f"Serveur central démarré sur "
            f"{self.host}:{self.port}"
        )

        try:
            while True:
                client_socket, client_address = server_socket.accept()

                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                ).start()

        except KeyboardInterrupt:
            print("\nServeur arrêté.")

        finally:
            server_socket.close()


def main():
    parser = argparse.ArgumentParser(
        description="Serveur central TCP/IP P2P"
    )

    parser.add_argument(
        "port",
        type=int,
        nargs="?",
        default=DEFAULT_PORT,
        help="Port d'écoute du serveur",
    )

    args = parser.parse_args()

    server = CentralServer(port=args.port)
    server.start()


if __name__ == "__main__":
    main()