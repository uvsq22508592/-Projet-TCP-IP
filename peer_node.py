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
        self.file_server_socket = None
        self.file_server_ready = threading.Event()
        self.file_server_error = None
        self.stop_event = threading.Event()

        if not os.path.isfile(self.shared_dir):
            os.makedirs(self.shared_dir, exist_ok=True)

    def central_request(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
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

    def list_files(self):
        return self.central_request({
            "cmd": "LIST_FILES",
        })

    def download_file(
        self,
        peer_host,
        peer_port,
        filename,
        destination_path,
        owner=None,
    ):
        """Download a shared file from another peer."""
        destination_path = os.path.abspath(destination_path)
        destination_dir = os.path.dirname(destination_path)
        os.makedirs(destination_dir, exist_ok=True)

        transfer_status = "FAILED"
        received_size = 0
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((peer_host, int(peer_port)))
                send_json(sock, {
                    "cmd": "GET_FILE",
                    "filename": filename,
                })

                response = recv_json(sock)
                if response is None:
                    raise ConnectionError("Réponse du peer absente")

                if response.get("status") != "OK":
                    raise RuntimeError(response.get(
                        "message",
                        "Téléchargement refusé",
                    ))

                expected_size = response.get("size")
                if not isinstance(expected_size, int) or expected_size < 0:
                    raise ValueError("Taille de fichier invalide")

                with open(destination_path, "wb") as file:
                    while received_size < expected_size:
                        data = sock.recv(
                            min(65536, expected_size - received_size)
                        )
                        if not data:
                            raise ConnectionError(
                                "Connexion interrompue pendant le téléchargement"
                            )
                        file.write(data)
                        received_size += len(data)

            transfer_status = "SUCCESS"
        except Exception:
            raise
        finally:
            try:
                self.central_request({
                    "cmd": "DOWNLOAD_EVENT",
                    "username": self.username,
                    "password": self.password,
                    "owner": owner or "",
                    "filename": os.path.basename(filename),
                    "relative_path": filename,
                    "size": received_size,
                    "status": transfer_status,
                })
            except OSError:
                pass

        return {
            "status": "OK",
            "filename": response.get("filename", os.path.basename(filename)),
            "size": received_size,
            "path": destination_path,
        }

    def ping(self):
        return self.central_request({
            "cmd": "PING",
            "username": self.username,
        })

    def start_file_server(self):
        self.file_server_ready.clear()
        self.file_server_error = None
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_server_socket = server
        try:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.peer_host, self.peer_port))
            server.listen(10)
            server.settimeout(0.5)
        except OSError as error:
            self.file_server_error = error
            self.file_server_ready.set()
            server.close()
            self.file_server_socket = None
            return

        self.file_server_ready.set()

        print(
            f"Peer démarré sur "
            f"{self.peer_host}:{self.peer_port}"
        )

        while not self.stop_event.is_set():
            try:
                client, address = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            threading.Thread(
                target=self.send_file,
                args=(client, address),
                daemon=True,
            ).start()

        server.close()
        self.file_server_socket = None

    def send_file(self, client, address):
        try:
            request = recv_json(client)

            if request.get("cmd") != "GET_FILE":
                send_json(client, {
                    "status": "ERROR",
                    "message": "Commande invalide",
                })
                return

            requested_path = request.get("filename", "")
            relative_path = os.path.normpath(requested_path)
            shared_path = os.path.realpath(self.shared_dir)
            if relative_path in ("", "."):
                send_json(client, {
                    "status": "ERROR",
                    "message": "Chemin de fichier invalide",
                })
                return

            if os.path.isfile(shared_path):
                if relative_path != os.path.basename(shared_path):
                    send_json(client, {
                        "status": "ERROR",
                        "message": "Chemin de fichier invalide",
                    })
                    return
                path = shared_path
            else:
                path = os.path.realpath(
                    os.path.join(shared_path, relative_path)
                )
                if os.path.commonpath((shared_path, path)) != shared_path:
                    send_json(client, {
                        "status": "ERROR",
                        "message": "Chemin de fichier invalide",
                    })
                    return

            if not os.path.isfile(path):
                send_json(client, {
                    "status": "ERROR",
                    "message": "Fichier introuvable",
                })
                return

            size = os.path.getsize(path)

            send_json(client, {
                "status": "OK",
                "filename": relative_path,
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
        self.stop_event.clear()
        threading.Thread(
            target=self.start_file_server,
            daemon=True,
        ).start()

        self.file_server_ready.wait(2)
        if self.file_server_error is not None:
            print(f"Erreur serveur peer : {self.file_server_error}")
            return

        login_result = self.login()
        print("Connexion :", login_result)

        if login_result.get("status") != "OK":
            return

        publish_result = self.publish_files()
        print("Publication :", publish_result)

        while not self.stop_event.is_set():
            time.sleep(30)
            if not self.stop_event.is_set():
                self.ping()

    def logout_peer(self):
        self.stop_event.set()
        if self.file_server_socket is not None:
            try:
                self.file_server_socket.close()
            except OSError:
                pass
        return self.central_request({
            "cmd": "LOGOUT",
            "username": self.username,
        })


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
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--download-host")
    parser.add_argument("--download-port", type=int)
    parser.add_argument("--download-file")
    parser.add_argument("--output")

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

    if args.list:
        print("Fichiers publiés :", peer.list_files())
        return

    if args.download_file:
        if not args.download_host or not args.download_port:
            parser.error(
                "--download-host et --download-port sont requis "
                "pour un téléchargement"
            )

        output = args.output or os.path.basename(args.download_file)
        try:
            result = peer.download_file(
                args.download_host,
                args.download_port,
                args.download_file,
                output,
            )
        except (ConnectionError, OSError, RuntimeError, ValueError) as error:
            parser.error(str(error))

        print("Téléchargement :", result)
        return

    if args.login:
        peer.start()
        return

    parser.print_help()


if __name__ == "__main__":
    main()