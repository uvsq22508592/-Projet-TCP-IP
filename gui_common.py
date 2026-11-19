import tkinter as tk
from tkinter import ttk


COLORS = {
    "background": "#111827",
    "surface": "#1f2937",
    "surface_light": "#374151",
    "text": "#f9fafb",
    "muted": "#9ca3af",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "danger": "#dc2626",
    "success": "#16a34a",
}


def configure_theme(root):
    root.configure(background=COLORS["background"])

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        ".",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "Card.TFrame",
        background=COLORS["surface"],
        relief="flat",
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI", 20, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("Segoe UI", 11, "bold"),
    )
    style.configure(
        "CardValue.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("Segoe UI", 24, "bold"),
    )
    style.configure(
        "Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        rowheight=28,
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["surface_light"],
        foreground=COLORS["text"],
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary"])],
        foreground=[("selected", "white")],
    )


def create_card(parent, title):
    card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
    value = ttk.Label(card, text="0", style="CardValue.TLabel")
    value.pack(anchor="w", pady=(8, 0))
    return card, value


def make_button(parent, text, command, danger=False):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        relief="flat",
        cursor="hand2",
        padx=14,
        pady=8,
        background=COLORS["danger"] if danger else COLORS["primary"],
        foreground="white",
        activebackground=COLORS["danger"] if danger else COLORS["primary_hover"],
        activeforeground="white",
        borderwidth=0,
        font=("Segoe UI", 10, "bold"),
    )
    return button
