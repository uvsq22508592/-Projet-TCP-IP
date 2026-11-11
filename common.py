import hashlib
import json
import os
import re
import socket


DEFAULT_PORT = 5000


def sha256_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def keywords_from_text(text):
    return [
        word.lower()
        for word in re.findall(
            r"[A-Za-z0-9À-ÿ]+",
            text or "",
        )
    ]


def send_json(sock, data):
    message = json.dumps(
        data,
        ensure_ascii=False,
    ).encode("utf-8")

    header = len(message).to_bytes(
        4,
        byteorder="big",
    )

    sock.sendall(header + message)


def recv_exact(sock, size):
    data = b""

    while len(data) < size:
        chunk = sock.recv(size - len(data))

        if not chunk:
            return None

        data += chunk

    return data


def recv_json(sock):
    header = recv_exact(sock, 4)

    if header is None:
        return None

    size = int.from_bytes(
        header,
        byteorder="big",
    )

    message = recv_exact(sock, size)

    if message is None:
        return None

    return json.loads(
        message.decode("utf-8")
    )


def list_shared_files(shared_dir):
    files = []

    for root, _, filenames in os.walk(shared_dir):
        for filename in filenames:
            path = os.path.join(root, filename)

            files.append({
                "name": filename,
                "relative_path": os.path.relpath(
                    path,
                    shared_dir,
                ),
                "size": os.path.getsize(path),
                "description": (
                    f"Fichier partagé : {filename}"
                ),
            })

    return files