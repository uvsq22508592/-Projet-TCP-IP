import argparse
import threading
import tkinter as tk
from tkinter import ttk

from gui_common import COLORS, configure_theme, create_card, make_button
from server_central import CentralServer


class CentralGui:
    def __init__(self, root, port):
        self.root = root
        self.port = port
        self.server = CentralServer(port=port)
        self.server_thread = None
        self.running = False

        self.root.title("P2P - Tableau de bord central")
        self.root.geometry("820x560")
        configure_theme(self.root)
        self.build()

    def build(self):
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Serveur central", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text=f"Indexation P2P - écoute sur le port {self.port}",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 20))

        cards = ttk.Frame(main)
        cards.pack(fill="x")
        cards.columnconfigure((0, 1, 2), weight=1)
        self.users_card, self.users_value = create_card(cards, "UTILISATEURS")
        self.peers_card, self.peers_value = create_card(cards, "PEERS ACTIFS")
        self.index_card, self.index_value = create_card(cards, "MOTS INDEXÉS")
        self.users_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.peers_card.grid(row=0, column=1, sticky="nsew", padx=8)
        self.index_card.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        toolbar = ttk.Frame(main)
        toolbar.pack(fill="x", pady=(18, 10))
        self.status = tk.Label(
            toolbar,
            text="● Arrêté",
            bg=COLORS["background"],
            fg=COLORS["danger"],
            font=("Segoe UI", 10, "bold"),
        )
        self.status.pack(side="left")
        self.start_button = make_button(toolbar, "Démarrer", self.start)
        self.start_button.pack(side="right")
        self.stop_button = make_button(toolbar, "Arrêter", self.stop, danger=True)

        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True)
        columns = ("Utilisateur", "Adresse", "Port", "Fichiers")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=150)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()

    def start(self):
        if self.running:
            return
        self.running = True
        self.status.configure(text="● En fonctionnement", fg=COLORS["success"])
        self.start_button.pack_forget()
        self.stop_button.pack(side="right")
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()

    def stop(self):
        if not self.running:
            return
        self.server.stop()
        self.running = False
        self.status.configure(text="● Arrêté", fg=COLORS["danger"])
        self.stop_button.pack_forget()
        self.start_button.pack(side="right")

    def refresh(self):
        snapshot = self.server.snapshot()
        self.users_value.configure(text=str(len(snapshot["users"])))
        self.peers_value.configure(text=str(len(snapshot["peers"])))
        self.index_value.configure(text=str(snapshot["indexed"]))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for peer in snapshot["peers"]:
            self.tree.insert(
                "",
                "end",
                values=(
                    peer["username"],
                    peer["host"],
                    peer["port"],
                    peer["files"],
                ),
            )
        self.root.after(1000, self.refresh)

    def close(self):
        self.stop()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", type=int, default=5000)
    args = parser.parse_args()

    root = tk.Tk()
    CentralGui(root, args.port)
    root.mainloop()


if __name__ == "__main__":
    main()
