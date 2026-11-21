import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui_common import COLORS, configure_theme, make_button
from peer_node import PeerNode


class PeerGui:
    def __init__(self, root):
        self.root = root
        self.peer = None
        self.running = False
        self.search_results = []

        self.root.title("P2P - Client")
        self.root.geometry("980x620")
        configure_theme(self.root)
        self.build()

    def build(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="Espace Peer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text="Connexion, publication et téléchargement de fichiers",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 16))

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)
        self.connection_tab = ttk.Frame(self.notebook, padding=18)
        self.search_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.connection_tab, text="Connexion")
        self.notebook.add(self.search_tab, text="Recherche")
        self.build_connection()
        self.build_search()

    def build_connection(self):
        form = ttk.Frame(self.connection_tab)
        form.pack(fill="x")
        form.columnconfigure((0, 1), weight=1)

        self.username = self.field(form, "Utilisateur", 0, 0)
        self.password = self.field(form, "Mot de passe", 0, 1, show="*")
        self.central_host = self.field(form, "Serveur central", 1, 0, "127.0.0.1")
        self.central_port = self.field(form, "Port central", 1, 1, "5000")
        self.peer_host = self.field(form, "Adresse du peer", 2, 0, "127.0.0.1")
        self.peer_port = self.field(form, "Port du peer", 2, 1, "6001")

        shared_row = ttk.Frame(self.connection_tab)
        shared_row.pack(fill="x", pady=(18, 12))
        ttk.Label(shared_row, text="Dossier partagé").pack(side="left")
        self.shared_dir = tk.StringVar(value=os.path.abspath("shared"))
        tk.Entry(
            shared_row,
            textvariable=self.shared_dir,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            width=56,
        ).pack(side="left", padx=10, fill="x", expand=True)
        make_button(shared_row, "Parcourir", self.choose_directory).pack(side="left")

        actions = ttk.Frame(self.connection_tab)
        actions.pack(fill="x", pady=10)
        make_button(actions, "S'inscrire", self.register).pack(side="left")
        make_button(actions, "Se connecter", self.login).pack(side="left", padx=8)
        make_button(actions, "Actualiser les fichiers", self.publish).pack(
            side="left",
            padx=8,
        )
        self.logout_button = make_button(actions, "Se déconnecter", self.logout, danger=True)

        self.status = tk.Label(
            self.connection_tab,
            text="● Hors ligne",
            bg=COLORS["background"],
            fg=COLORS["danger"],
            font=("Segoe UI", 10, "bold"),
        )
        self.status.pack(anchor="w", pady=(14, 0))

    def field(self, parent, label, row, column, value="", show=None):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="ew", padx=(0, 12), pady=6)
        ttk.Label(frame, text=label).pack(anchor="w", pady=(0, 5))
        variable = tk.StringVar(value=value)
        entry = tk.Entry(
            frame,
            textvariable=variable,
            show=show,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
        )
        entry.pack(fill="x", ipady=7)
        return variable

    def build_search(self):
        search_row = ttk.Frame(self.search_tab)
        search_row.pack(fill="x")
        ttk.Label(search_row, text="Mot-clé").pack(side="left")
        self.query = tk.StringVar()
        tk.Entry(
            search_row,
            textvariable=self.query,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
        ).pack(side="left", fill="x", expand=True, padx=10, ipady=7)
        make_button(search_row, "Rechercher", self.search).pack(side="left")
        make_button(search_row, "Afficher tous", self.list_all).pack(
            side="left",
            padx=(8, 0),
        )

        table_frame = ttk.Frame(self.search_tab)
        table_frame.pack(fill="both", expand=True, pady=(14, 0))
        columns = ("Fichier", "Utilisateur", "Adresse", "Port", "Description")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.configure(selectmode="extended")
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=170)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _event: self.download_selected())

        make_button(self.search_tab, "Télécharger la sélection", self.download_selected).pack(
            anchor="e",
            pady=(12, 0),
        )

    def choose_directory(self):
        directory = filedialog.askdirectory(initialdir=self.shared_dir.get())
        if directory:
            self.shared_dir.set(directory)

    def create_peer(self):
        try:
            return PeerNode(
                username=self.username.get().strip(),
                password=self.password.get(),
                shared_dir=self.shared_dir.get(),
                central_host=self.central_host.get().strip(),
                central_port=int(self.central_port.get()),
                peer_host=self.peer_host.get().strip(),
                peer_port=int(self.peer_port.get()),
            )
        except ValueError as error:
            messagebox.showerror("Configuration invalide", str(error))
            return None

    def register(self):
        peer = self.create_peer()
        if peer:
            try:
                result = peer.register()
                messagebox.showinfo("Inscription", result.get("message", ""))
            except OSError as error:
                messagebox.showerror("Connexion impossible", str(error))

    def login(self):
        if self.running:
            return
        peer = self.create_peer()
        if peer is None:
            return
        try:
            self.peer = peer
            threading.Thread(target=peer.start_file_server, daemon=True).start()
            if not peer.file_server_ready.wait(2):
                raise ConnectionError("Le serveur de fichiers ne démarre pas")
            if peer.file_server_error is not None:
                raise peer.file_server_error

            login_result = peer.login()
            if login_result.get("status") != "OK":
                messagebox.showerror("Connexion", login_result.get("message", "Échec"))
                peer.logout_peer()
                self.peer = None
                return
            publish_result = peer.publish_files()
            if publish_result.get("status") != "OK":
                messagebox.showerror(
                    "Publication",
                    publish_result.get("message", "Publication impossible"),
                )
                peer.logout_peer()
                self.peer = None
                return
            threading.Thread(target=peer_ping_loop, args=(peer,), daemon=True).start()
            self.running = True
            self.status.configure(text="● En ligne", fg=COLORS["success"])
            self.logout_button.pack(side="left", padx=8)
        except OSError as error:
            self.peer = None
            messagebox.showerror("Connexion impossible", str(error))

    def publish(self):
        if self.peer is None or not self.running:
            messagebox.showwarning(
                "Publication",
                "Connectez-vous avant de publier les fichiers.",
            )
            return
        try:
            result = self.peer.publish_files()
            if result.get("status") != "OK":
                messagebox.showerror(
                    "Publication",
                    result.get("message", "Publication impossible"),
                )
                return
            messagebox.showinfo("Publication", result.get("message", "Fichiers publiés"))
        except OSError as error:
            messagebox.showerror("Publication impossible", str(error))

    def logout(self):
        if not self.running or self.peer is None:
            return
        try:
            self.peer.logout_peer()
        except OSError:
            pass
        self.running = False
        self.status.configure(text="● Hors ligne", fg=COLORS["danger"])
        self.logout_button.pack_forget()

    def search(self):
        if self.peer is None:
            peer = self.create_peer()
        else:
            peer = self.peer
        if peer is None:
            return
        try:
            result = peer.search(self.query.get())
        except OSError as error:
            messagebox.showerror("Recherche impossible", str(error))
            return
        if result.get("status") != "OK":
            messagebox.showerror("Recherche", result.get("message", "Échec"))
            return

        self.display_results(result.get("results", []))

    def list_all(self):
        peer = self.peer if self.peer is not None else self.create_peer()
        if peer is None:
            return
        try:
            result = peer.list_files()
        except OSError as error:
            messagebox.showerror("Affichage impossible", str(error))
            return
        if result.get("status") != "OK":
            messagebox.showerror(
                "Affichage",
                result.get("message", "Impossible de lister les fichiers"),
            )
            return
        self.display_results(result.get("results", []))

    def display_results(self, results):
        self.search_results = results
        for item in self.tree.get_children():
            self.tree.delete(item)
        for file_info in self.search_results:
            self.tree.insert(
                "",
                "end",
                values=(
                    file_info["filename"],
                    file_info["username"],
                    file_info["peer_host"],
                    file_info["peer_port"],
                    file_info.get("description", ""),
                ),
            )

    def download_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Téléchargement", "Sélectionnez un fichier.")
            return

        peer = self.peer or self.create_peer()
        if peer is None:
            return

        if len(selection) == 1:
            index = self.tree.index(selection[0])
            file_info = self.search_results[index]
            destination = filedialog.asksaveasfilename(
                initialfile=file_info["filename"],
            )
            if not destination:
                return
            try:
                result = peer.download_file(
                    file_info["peer_host"],
                    file_info["peer_port"],
                    file_info.get("relative_path", file_info["filename"]),
                    destination,
                    owner=file_info["username"],
                )
                messagebox.showinfo(
                    "Téléchargement",
                    f"Fichier enregistré :\n{result['path']}",
                )
            except (ConnectionError, OSError, RuntimeError, ValueError) as error:
                messagebox.showerror("Téléchargement impossible", str(error))
            return

        destination_dir = filedialog.askdirectory(
            title="Choisir le dossier de destination",
        )
        if not destination_dir:
            return

        successes = 0
        failures = []
        for item in selection:
            index = self.tree.index(item)
            file_info = self.search_results[index]
            relative_path = file_info.get(
                "relative_path",
                file_info["filename"],
            )
            destination = os.path.abspath(
                os.path.join(
                    destination_dir,
                    file_info["username"],
                    relative_path,
                )
            )
            try:
                peer.download_file(
                    file_info["peer_host"],
                    file_info["peer_port"],
                    relative_path,
                    destination,
                    owner=file_info["username"],
                )
                successes += 1
            except (ConnectionError, OSError, RuntimeError, ValueError) as error:
                failures.append(
                    f"{relative_path}: {error}"
                )

        message = f"{successes} fichier(s) téléchargé(s)."
        if failures:
            message += "\n\n" + "\n".join(failures)
        messagebox.showinfo("Téléchargements multiples", message)

    def close(self):
        self.logout()
        self.root.destroy()


def peer_ping_loop(peer):
    while not peer.stop_event.is_set():
        peer.stop_event.wait(30)
        if not peer.stop_event.is_set():
            try:
                peer.ping()
            except OSError:
                return


def main():
    root = tk.Tk()
    gui = PeerGui(root)
    root.protocol("WM_DELETE_WINDOW", gui.close)
    root.mainloop()


if __name__ == "__main__":
    main()
