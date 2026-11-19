import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from gui_common import COLORS, configure_theme, make_button


class Launcher:
    def __init__(self, root):
        self.root = root
        self.project_dir = Path(__file__).resolve().parent
        self.root.title("P2P - Lanceur")
        self.root.geometry("520x360")
        configure_theme(self.root)

        frame = ttk.Frame(root, padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Projet P2P", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            frame,
            text="Partage de fichiers TCP/IP",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(6, 28))

        cards = ttk.Frame(frame)
        cards.pack(fill="both", expand=True)

        central = ttk.Frame(cards, style="Card.TFrame", padding=20)
        central.pack(fill="x", pady=8)
        ttk.Label(
            central,
            text="Serveur central",
            style="CardTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            central,
            text="Authentification, indexation et sessions",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
        ).pack(anchor="w", pady=(8, 12))
        make_button(
            central,
            "Ouvrir le tableau de bord",
            lambda: self.launch("central_gui.py"),
        ).pack(anchor="w")

        peer = ttk.Frame(cards, style="Card.TFrame", padding=20)
        peer.pack(fill="x", pady=8)
        ttk.Label(
            peer,
            text="Client / Peer",
            style="CardTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            peer,
            text="Recherche, publication et téléchargement",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
        ).pack(anchor="w", pady=(8, 12))
        make_button(
            peer,
            "Ouvrir le client",
            lambda: self.launch("peer_gui.py"),
        ).pack(anchor="w")

    def launch(self, script):
        subprocess.Popen(
            [sys.executable, str(self.project_dir / script)],
            cwd=str(self.project_dir),
        )


if __name__ == "__main__":
    root = tk.Tk()
    Launcher(root)
    root.mainloop()
