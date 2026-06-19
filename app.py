import base64
import json
import os

import customtkinter as ctk

# ---------- Constants ----------

FILE_CONTACTS = "contacts.json"
FILE_FAVORITES = "favorites.json"
FILE_SECRET = "secret.json"

DEFAULT_CONTACTS = {"Ivan": "+79991112233", "Anna": "+79994445566"}

COLOR_PRIMARY = "#1f6aa5"
COLOR_PRIMARY_HOVER = "#144870"
COLOR_SUCCESS = "#2cb67d"
COLOR_SUCCESS_HOVER = "#1e8557"
COLOR_DANGER = "#e55039"
COLOR_DANGER_HOVER = "#b83b26"
COLOR_GRAY = "gray"
COLOR_GRAY_HOVER = "#555555"


# ---------- Encryption helpers ----------

def _xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode("utf-8")
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))


def encrypt_data(data_str: str, key: str) -> str:
    if not key:
        return data_str
    encrypted = _xor_bytes(data_str.encode("utf-8"), key)
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_data(encoded_str: str, key: str) -> str:
    if not key:
        return encoded_str
    try:
        raw = base64.b64decode(encoded_str.encode("utf-8"))
        return _xor_bytes(raw, key).decode("utf-8")
    except Exception:
        return "{}"


# ---------- Persistence helpers ----------

def load_json(path, key, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        return json.loads(decrypt_data(content, key))
    except Exception:
        return default


def save_json(path, data, key):
    raw_json = json.dumps(data, ensure_ascii=False, indent=4)
    with open(path, "w", encoding="utf-8") as f:
        f.write(encrypt_data(raw_json, key))


def save_contacts():
    save_json(FILE_CONTACTS, contacts, current_key)


def save_favorites():
    save_json(FILE_FAVORITES, favorites, current_key)


def load_secret():
    if os.path.exists(FILE_SECRET):
        with open(FILE_SECRET, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"password": ""}


secret_data = load_secret()
current_key = secret_data["password"]
contacts = load_json(FILE_CONTACTS, current_key, dict(DEFAULT_CONTACTS))
favorites = load_json(FILE_FAVORITES, current_key, [])


# ---------- Reusable dialog helpers ----------

def make_toplevel(title, size, parent=None):
    win = ctk.CTkToplevel(parent or app)
    win.title(title)
    win.geometry(size)
    win.resizable(False, False)
    win.attributes("-topmost", True)
    return win


def confirm_dialog(message, on_confirm, parent=None, title="Confirm"):
    win = make_toplevel(title, "280x130", parent)

    ctk.CTkLabel(master=win, text=message, font=("Arial", 14)).pack(pady=15)

    btn_frame = ctk.CTkFrame(master=win, fg_color="transparent")
    btn_frame.pack()

    def yes():
        on_confirm()
        win.destroy()

    ctk.CTkButton(master=btn_frame, text="Yes", width=80, fg_color=COLOR_DANGER,
                  hover_color=COLOR_DANGER_HOVER, command=yes).pack(side="left", padx=10)
    ctk.CTkButton(master=btn_frame, text="No", width=80, fg_color=COLOR_GRAY,
                  hover_color=COLOR_GRAY_HOVER, command=win.destroy).pack(side="left", padx=10)
    return win


def open_edit_window(name, phone, refresh_callback):
    win = make_toplevel("Edit contact", "300x250")

    ctk.CTkLabel(master=win, text=f"Edit {name}", font=("Arial", 16, "bold")).pack(pady=15)

    phone_entry = ctk.CTkEntry(master=win, width=250)
    phone_entry.insert(0, phone)
    phone_entry.pack(pady=10)

    error_label = ctk.CTkLabel(master=win, text="", font=("Arial", 12))
    error_label.pack(pady=5)

    def save_edit():
        new_phone = phone_entry.get().strip()
        if not new_phone:
            error_label.configure(text="Please fill in the number!", text_color="red")
            return
        if not new_phone.isdigit():
            error_label.configure(text="The number must consist of digits!", text_color="red")
            return
        contacts[name] = new_phone
        save_contacts()
        refresh_callback()
        win.destroy()

    ctk.CTkButton(master=win, text="Save", width=150, height=35, corner_radius=8,
                  fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                  command=save_edit).pack(pady=10)


def delete_contact(name, refresh_callback):
    def do_delete():
        del contacts[name]
        if name in favorites:
            favorites.remove(name)
            save_favorites()
        save_contacts()
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
        refresh_callback()

    confirm_dialog(f"Delete contact '{name}'?", do_delete)


# ---------- Contact list rendering ----------

def render_contact_row(parent, name, phone, refresh_callback, highlight=False):
    row = ctk.CTkFrame(master=parent, fg_color="transparent")
    row.pack(fill="x", padx=5, pady=3)

    prefix = "⭐ " if name in favorites else "👤 "
    label_kwargs = (
        {"font": ("Arial", 14, "bold"), "text_color": "#2cb67d"}
        if highlight else
        {"font": ("Arial", 14)}
    )

    ctk.CTkLabel(master=row, text=f"{prefix}{name}: {phone}", anchor="w", **label_kwargs).pack(
        side="left", fill="x", expand=True, padx=5)

    ctk.CTkButton(master=row, text="❌", width=30, height=25, fg_color=COLOR_DANGER,
                  hover_color=COLOR_DANGER_HOVER, font=("Arial", 10, "bold"),
                  command=lambda: delete_contact(name, refresh_callback)).pack(side="right", padx=5)

    ctk.CTkButton(master=row, text="✏️", width=30, height=25, fg_color=COLOR_PRIMARY,
                  hover_color=COLOR_PRIMARY_HOVER, font=("Arial", 10, "bold"),
                  command=lambda: open_edit_window(name, phone, refresh_callback)).pack(side="right", padx=5)


def display_contacts(items, refresh_callback, highlight=False, empty_message=None):
    for widget in contacts_frame.winfo_children():
        widget.destroy()

    if not items and empty_message:
        ctk.CTkLabel(master=contacts_frame, text=empty_message, font=("Arial", 14, "italic"),
                     text_color="gray").pack(pady=20)
        return

    for name, phone in items:
        render_contact_row(contacts_frame, name, phone, refresh_callback, highlight)


def show_all_contacts():
    display_contacts(sorted(contacts.items()), show_all_contacts)


def search_contact():
    query = search_entry.get().strip().lower()
    if not query:
        show_all_contacts()
        return

    matches = [(n, p) for n, p in contacts.items() if query in n.lower() or query in p.lower()]
    display_contacts(matches, search_contact, highlight=True, empty_message="Nothing found")


# ---------- Add contact ----------

def open_add_contact_window():
    win = make_toplevel("Add a contact", "300x350")

    ctk.CTkLabel(master=win, text="New contact", font=("Arial", 16, "bold")).pack(pady=15)

    name_entry = ctk.CTkEntry(master=win, placeholder_text="Contact name", width=250)
    name_entry.pack(pady=10)

    phone_entry = ctk.CTkEntry(master=win, placeholder_text="Phone number (numbers only)", width=250)
    phone_entry.pack(pady=10)

    error_label = ctk.CTkLabel(master=win, text="", font=("Arial", 12))
    error_label.pack(pady=5)

    def save_new_contact():
        name = name_entry.get().strip().title()
        phone = phone_entry.get().strip()

        if not name or not phone:
            error_label.configure(text="Please fill in all fields!", text_color="red")
            return
        if name in contacts:
            error_label.configure(text="This contact name already exists! ⚠️", text_color="yellow")
            return
        if not phone.isdigit():
            error_label.configure(text="The number must consist of digits!", text_color="red")
            return

        contacts[name] = phone
        save_contacts()
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
        show_all_contacts()
        win.destroy()

    ctk.CTkButton(master=win, text="Save", width=150, height=35, corner_radius=8,
                  fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                  command=save_new_contact).pack(pady=10)



def open_favorites_window():
    fav_window = make_toplevel("Favorites", "400x450")

    ctk.CTkLabel(master=fav_window, text="⭐ Favorite Contacts", font=("Arial", 20, "bold")).pack(pady=15)

    fav_entry = ctk.CTkEntry(master=fav_window, placeholder_text="Type name from list to add...", width=250)
    fav_entry.pack(pady=5)

    fav_scroll = ctk.CTkScrollableFrame(master=fav_window, width=320, height=200, corner_radius=8)
    fav_scroll.pack(pady=15)

    def refresh_fav_list():
        for widget in fav_scroll.winfo_children():
            widget.destroy()

        if not favorites:
            ctk.CTkLabel(master=fav_scroll, text="Favorites list is empty", font=("Arial", 14, "italic"),
                         text_color="gray").pack(pady=20)
            return

        for name in sorted(favorites):
            if name not in contacts:
                continue
            row = ctk.CTkFrame(master=fav_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=3)

            ctk.CTkLabel(master=row, text=f"⭐ {name}: {contacts[name]}", font=("Arial", 14),
                         anchor="w").pack(side="left", fill="x", expand=True, padx=5)

            def remove_fav(n=name):
                favorites.remove(n)
                save_favorites()
                refresh_fav_list()
                show_all_contacts()

            ctk.CTkButton(master=row, text="🗑️", width=30, height=25, fg_color=COLOR_DANGER,
                          hover_color=COLOR_DANGER_HOVER, font=("Arial", 10),
                          command=remove_fav).pack(side="right", padx=5)

    def add_to_fav():
        query = fav_entry.get().strip().lower()
        if not query:
            return

        matches = [name for name in contacts if query in name.lower() and name not in favorites]

        if not matches:
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="No new matches found!", placeholder_text_color="red")
            return

        if len(matches) > 1:
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="Multiple found! Be more specific.", placeholder_text_color="yellow")
            return

        name_to_add = matches[0]

        def confirm_add():
            favorites.append(name_to_add)
            save_favorites()
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="Type name from list to add...", placeholder_text_color="gray")
            refresh_fav_list()
            show_all_contacts()

        confirm_dialog(f"Add '{name_to_add}' to favorites?", confirm_add, parent=fav_window)

    ctk.CTkButton(master=fav_window, text="Add to favorites", width=150, height=30, fg_color=COLOR_PRIMARY,
                  command=add_to_fav).pack(pady=5)

    refresh_fav_list()


# ---------- Clear all ----------

def clear_all_contacts_window():
    if not contacts:
        return

    def do_clear():
        contacts.clear()
        favorites.clear()
        save_contacts()
        save_favorites()
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
        show_all_contacts()

    confirm_dialog("Delete ALL contacts?", do_clear, title="Clear Book")

def open_password_window():
    global current_key, contacts, favorites

    win = make_toplevel("Password Management", "300x200")
    is_set = bool(secret_data["password"])

    lbl = ctk.CTkLabel(master=win, text="Enter Password" if is_set else "Set Master Password",
                        font=("Arial", 16, "bold"))
    lbl.pack(pady=15)

    pass_entry = ctk.CTkEntry(master=win, placeholder_text="Password...", width=200, show="*")
    pass_entry.pack(pady=10)

    def handle_password():
        global current_key, contacts, favorites
        entered = pass_entry.get().strip()
        if not entered:
            return

        if is_set:
            if entered != secret_data["password"]:
                lbl.configure(text="Wrong Password! ❌", text_color="red")
                return
            current_key = entered
            contacts = load_json(FILE_CONTACTS, current_key, contacts)
            favorites = load_json(FILE_FAVORITES, current_key, favorites)
        else:
            secret_data["password"] = entered
            current_key = entered
            with open(FILE_SECRET, "w", encoding="utf-8") as f:
                json.dump(secret_data, f, ensure_ascii=False, indent=4)
            save_contacts()
            save_favorites()

        show_all_contacts()
        win.destroy()

    ctk.CTkButton(master=win, text="Confirm", width=120, command=handle_password).pack(pady=10)


# ---------- UI setup ----------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Phonebook v1.0")
app.geometry("500x600")
app.resizable(False, False)

ctk.CTkLabel(master=app, text="Telephone directory", font=("Arial", 24, "bold")).pack(pady=20)

search_entry = ctk.CTkEntry(master=app, placeholder_text="Enter a name or number to search...",
                             width=350, height=40, corner_radius=8)
search_entry.pack(pady=10)
search_entry.bind("<KeyRelease>", lambda event: search_contact())

contacts_frame = ctk.CTkScrollableFrame(
    master=app, width=350, height=250, corner_radius=8,
    label_text=f"Contact list ({len(contacts)})", label_font=("Arial", 12, "bold")
)
contacts_frame.pack(pady=20)

btn_frame = ctk.CTkFrame(master=app, fg_color="transparent")
btn_frame.pack(pady=10)

ctk.CTkButton(master=btn_frame, text="Add contact", width=170, height=40, corner_radius=8,
              fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, font=("Arial", 14, "bold"),
              command=open_add_contact_window).pack(side="left", padx=5)

ctk.CTkButton(master=btn_frame, text="Favorites", width=170, height=40, corner_radius=8,
              fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, font=("Arial", 14, "bold"),
              command=open_favorites_window).pack(side="left", padx=5)

bottom_frame = ctk.CTkFrame(master=app, fg_color="transparent")
bottom_frame.pack(pady=5)

ctk.CTkButton(master=bottom_frame, text="🔐 Password", width=170, height=35, corner_radius=8,
              fg_color=COLOR_GRAY, hover_color=COLOR_GRAY_HOVER, font=("Arial", 13),
              command=open_password_window).pack(side="left", padx=5)

ctk.CTkButton(master=bottom_frame, text="🗑️ Clear all", width=170, height=35, corner_radius=8,
              fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER, font=("Arial", 13),
              command=clear_all_contacts_window).pack(side="left", padx=5)

show_all_contacts()
app.mainloop()