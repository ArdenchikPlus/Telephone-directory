import base64
import customtkinter as ctk
import json
import os

file_name = "contacts.json"
fav_file_name = "favorites.json"
secret_file = "secret.json"

def encrypt_decrypt(data_str, key):
    if not key:
        return data_str
    key_bytes = key.encode('utf-8')
    data_bytes = data_str.encode('utf-8')
    decrypted = bytearray(
        data_bytes[i] ^ key_bytes[i % len(key_bytes)]
        for i in range(len(data_bytes))
    )
    return base64.b64encode(decrypted).decode('utf-8')

def decrypt_data(encoded_str, key):
    if not key:
        return encoded_str
    try:
        data_bytes = base64.b64decode(encoded_str.encode('utf-8'))
        key_bytes = key.encode('utf-8')
        decrypted = bytearray(
            data_bytes[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data_bytes))
        )
        return decrypted.decode('utf-8')
    except Exception:
        return "{}"

if os.path.exists(secret_file):
    with open(secret_file, "r", encoding="utf-8") as file:
        secret_data = json.load(file)
else:
    secret_data = {"password": ""}

current_key = secret_data["password"]

def save_contacts(data):
    raw_json = json.dumps(data, ensure_ascii=False, indent=4)
    encrypted_str = encrypt_decrypt(raw_json, current_key)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(encrypted_str)

def save_favorites(data):
    raw_json = json.dumps(data, ensure_ascii=False, indent=4)
    encrypted_str = encrypt_decrypt(raw_json, current_key)
    with open(fav_file_name, "w", encoding="utf-8") as file:
        file.write(encrypted_str)

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()
    try:
        decrypted_str = decrypt_data(content, current_key)
        contacts = json.loads(decrypted_str)
    except Exception:
        contacts = {}
else:
    contacts = {"Ivan": "+79991112233", "Anna": "+79994445566"}

if os.path.exists(fav_file_name):
    with open(fav_file_name, "r", encoding="utf-8") as file:
        content = file.read()
    try:
        decrypted_str = decrypt_data(content, current_key)
        favorites = json.loads(decrypted_str)
    except Exception:
        favorites = []
else:
    favorites = []



def show_all_contacts():
    for widget in contacts_frame.winfo_children():
        widget.destroy()

    for name, phone in sorted(contacts.items()):
        row_frame = ctk.CTkFrame(master=contacts_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=5, pady=3)

        prefix = "⭐ " if name in favorites else "👤 "

        contact_label = ctk.CTkLabel(
            master=row_frame,
            text=f"{prefix}{name}: {phone}",
            font=("Arial", 14),
            anchor="w"
        )
        contact_label.pack(side="left", fill="x", expand=True, padx=5)

        def open_edit_window(n=name, p=phone):
            edit_window = ctk.CTkToplevel(app)
            edit_window.title("Edit contact")
            edit_window.geometry("300x250")
            edit_window.resizable(False, False)
            edit_window.attributes("-topmost", True)

            title_label = ctk.CTkLabel(master=edit_window, text=f"Edit {n}", font=("Arial", 16, "bold"))
            title_label.pack(pady=15)

            phone_entry = ctk.CTkEntry(master=edit_window, width=250)
            phone_entry.insert(0, p)
            phone_entry.pack(pady=10)

            def save_edited_contact():
                new_phone = phone_entry.get().strip()

                if not new_phone:
                    error_label.configure(text="Please fill in the number!", text_color="red")
                    return
                if not new_phone.isdigit():
                    error_label.configure(text="The number must consist of digits!", text_color="red")
                    return

                contacts[n] = new_phone
                save_contacts(contacts)
                show_all_contacts()
                edit_window.destroy()

            error_label = ctk.CTkLabel(master=edit_window, text="", font=("Arial", 12))
            error_label.pack(pady=5)

            save_button = ctk.CTkButton(master=edit_window, text="Save", width=150, height=35, corner_radius=8,
                                        fg_color="#1f6aa5", hover_color="#144870", command=save_edited_contact)
            save_button.pack(pady=10)

        def make_delete_cmd(n=name):
            confirm_window = ctk.CTkToplevel(app)
            confirm_window.title("Delete")
            confirm_window.geometry("280x130")
            confirm_window.resizable(False, False)
            confirm_window.attributes("-topmost", True)

            label = ctk.CTkLabel(master=confirm_window, text=f"Delete contact '{n}'?", font=("Arial", 14))
            label.pack(pady=15)

            btn_frame = ctk.CTkFrame(master=app, fg_color="transparent")
            btn_frame.pack(pady=10)

            add_contact_button = ctk.CTkButton(
                master=btn_frame,
                text="➕ Add contact",
                width=110,
                height=40,
                corner_radius=8,
                fg_color="#2cb67d",
                hover_color="#1e8557",
                font=("Arial", 12, "bold"),
                command=open_add_contact_window
            )
            add_contact_button.pack(side="left", padx=3)

            fav_button = ctk.CTkButton(
                master=btn_frame,
                text="⭐ Favorites",
                width=110,
                height=40,
                corner_radius=8,
                fg_color="#1f6aa5",
                hover_color="#144870",
                font=("Arial", 12, "bold"),
                command=open_favorites_window
            )
            fav_button.pack(side="left", padx=3)

            def clear_all_contacts_window():
                if not contacts:
                    return

                clear_window = ctk.CTkToplevel(app)
                clear_window.title("Clear Book")
                clear_window.geometry("280x130")
                clear_window.resizable(False, False)
                clear_window.attributes("-topmost", True)

                label = ctk.CTkLabel(master=clear_window, text="Delete ALL contacts?", font=("Arial", 14, "bold"),
                                     text_color="#e55039")
                label.pack(pady=15)

                c_btn_frame = ctk.CTkFrame(master=clear_window, fg_color="transparent")
                c_btn_frame.pack()

                def confirm_clear():
                    contacts.clear()
                    favorites.clear()
                    save_contacts(contacts)
                    save_favorites(favorites)
                    contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
                    show_all_contacts()
                    clear_window.destroy()

                yes_btn = ctk.CTkButton(master=c_btn_frame, text="Yes", width=80, fg_color="#e55039",
                                        hover_color="#b83b26", command=confirm_clear)
                yes_btn.pack(side="left", padx=10)
                no_btn = ctk.CTkButton(master=c_btn_frame, text="No", width=80, fg_color="gray", hover_color="#555555",
                                       command=clear_window.destroy)
                no_btn.pack(side="left", padx=10)

            clear_button = ctk.CTkButton(
                master=btn_frame,
                text="🗑️ Clear All",
                width=110,
                height=40,
                corner_radius=8,
                fg_color="#e55039",
                hover_color="#b83b26",
                font=("Arial", 12, "bold"),
                command=clear_all_contacts_window
            )
            clear_button.pack(side="left", padx=3)

            def confirm_delete():
                del contacts[n]
                if n in favorites:
                    favorites.remove(n)
                    save_favorites(favorites)
                save_contacts(contacts)
                contacts_frame.configure(label_text=f"Contact list ({len(contacts)})") # <--- СЮДА
                show_all_contacts()
                confirm_window.destroy()


            yes_btn = ctk.CTkButton(master=btn_frame, text="Yes", width=80, fg_color="#e55039", hover_color="#b83b26",
                                    command=confirm_delete)
            yes_btn.pack(side="left", padx=10)
            no_btn = ctk.CTkButton(master=btn_frame, text="No", width=80, fg_color="gray", hover_color="#555555",
                                   command=confirm_window.destroy)
            no_btn.pack(side="left", padx=10)

        delete_button = ctk.CTkButton(master=row_frame, text="❌", width=30, height=25, fg_color="#e55039",
                                      hover_color="#b83b26", font=("Arial", 10, "bold"), command=make_delete_cmd)
        delete_button.pack(side="right", padx=5)

        edit_button = ctk.CTkButton(master=row_frame, text="✏️", width=30, height=25, fg_color="#1f6aa5",
                                    hover_color="#144870", font=("Arial", 10, "bold"), command=open_edit_window)
        edit_button.pack(side="right", padx=5)


def search_contact():
    query = search_entry.get().strip().lower()

    if not query:
        show_all_contacts()
        return

    for widget in contacts_frame.winfo_children():
        widget.destroy()

    found = False

    for name, phone in contacts.items():
        if query in name.lower() or query in phone.lower():
            row_frame = ctk.CTkFrame(master=contacts_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=5, pady=3)

            prefix = "⭐" if name in favorites else "👤"

            contact_label = ctk.CTkLabel(
                master=row_frame,
                text=f"{prefix}{name}: {phone}",
                font=("Arial", 14, "bold"),
                text_color="#2cb67d",
                anchor="w"
            )
            contact_label.pack(side="left", fill="x", expand=True, padx=5)

            def make_delete_cmd(n=name):
                confirm_window = ctk.CTkToplevel(app)
                confirm_window.title("Delete")
                confirm_window.geometry("280x130")
                confirm_window.resizable(False, False)
                confirm_window.attributes("-topmost", True)

                label = ctk.CTkLabel(master=confirm_window, text=f"Delete contact '{n}'?", font=("Arial", 14))
                label.pack(pady=15)

                btn_frame = ctk.CTkFrame(master=confirm_window, fg_color="transparent")
                btn_frame.pack()

                def confirm_delete():
                    del contacts[n]
                    if n in favorites:
                        favorites.remove(n)
                        save_favorites(favorites)
                    save_contacts(contacts)
                    contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
                    search_contact()
                    confirm_window.destroy()

                yes_btn = ctk.CTkButton(master=btn_frame, text="Yes", width=80, fg_color="#e55039",
                                        hover_color="#b83b26", command=confirm_delete)
                yes_btn.pack(side="left", padx=10)
                no_btn = ctk.CTkButton(master=btn_frame, text="No", width=80, fg_color="gray", hover_color="#555555",
                                       command=confirm_window.destroy)
                no_btn.pack(side="left", padx=10)

            def open_edit_window(n=name, p=phone):
                edit_window = ctk.CTkToplevel(app)
                edit_window.title("Edit contact")
                edit_window.geometry("300x250")
                edit_window.resizable(False, False)
                edit_window.attributes("-topmost", True)

                title_label = ctk.CTkLabel(master=edit_window, text=f"Edit {n}", font=("Arial", 16, "bold"))
                title_label.pack(pady=15)

                phone_entry = ctk.CTkEntry(master=edit_window, width=250)
                phone_entry.insert(0, p)
                phone_entry.pack(pady=10)

                def save_edited_contact():
                    new_phone = phone_entry.get().strip()

                    if not new_phone:
                        error_label.configure(text="Please fill in the number!", text_color="red")
                        return
                    if not new_phone.isdigit():
                        error_label.configure(text="The number must consist of digits!", text_color="red")
                        return

                    contacts[n] = new_phone
                    save_contacts(contacts)
                    search_contact()
                    edit_window.destroy()

                error_label = ctk.CTkLabel(master=edit_window, text="", font=("Arial", 12))
                error_label.pack(pady=5)

                save_button = ctk.CTkButton(master=edit_window, text="Save", width=150, height=35, corner_radius=8,
                                            fg_color="#1f6aa5", hover_color="#144870", command=save_edited_contact)
                save_button.pack(pady=10)

            delete_button = ctk.CTkButton(master=row_frame, text="❌", width=30, height=25, fg_color="#e55039",
                                          hover_color="#b83b26", font=("Arial", 10, "bold"), command=make_delete_cmd)
            delete_button.pack(side="right", padx=5)

            edit_button = ctk.CTkButton(master=row_frame, text="✏️", width=30, height=25, fg_color="#1f6aa5",
                                        hover_color="#144870", font=("Arial", 10, "bold"), command=open_edit_window)
            edit_button.pack(side="right", padx=5)

            found = True

    if not found:
        no_result_label = ctk.CTkLabel(master=contacts_frame, text="Nothing found", font=("Arial", 14, "italic"),
                                       text_color="gray")
        no_result_label.pack(pady=20)


def open_add_contact_window():
    add_window = ctk.CTkToplevel(app)
    add_window.title("Add a contact")
    add_window.geometry("300x350")
    add_window.resizable(False, False)
    add_window.attributes("-topmost", True)

    title_label = ctk.CTkLabel(master=add_window, text="New contact", font=("Arial", 16, "bold"))
    title_label.pack(pady=15)

    name_entry = ctk.CTkEntry(master=add_window, placeholder_text="Contact name", width=250)
    name_entry.pack(pady=10)

    phone_entry = ctk.CTkEntry(master=add_window, placeholder_text="Phone number (numbers only)", width=250)
    phone_entry.pack(pady=10)

    def save_new_contact():
        name = name_entry.get().strip().title()
        phone = phone_entry.get().strip()

        if not name or not phone:
            error_label.configure(text="Please fill in all fields!", text_color="red")
            return
        if not phone.isdigit():
            error_label.configure(text="The number must consist of digits!", text_color="red")
            return

        contacts[name] = phone
        save_contacts(contacts)
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})") # <--- СЮДА
        show_all_contacts()
        add_window.destroy()


    error_label = ctk.CTkLabel(master=add_window, text="", font=("Arial", 12))
    error_label.pack(pady=5)

    save_button = ctk.CTkButton(master=add_window, text="Save", width=150, height=35, corner_radius=8,
                                fg_color="#2cb67d", hover_color="#1e8557", command=save_new_contact)
    save_button.pack(pady=10)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Phonebook v1.0")
app.geometry("500x600")
app.resizable(False, False)

title_label = ctk.CTkLabel(master=app, text="Telephone directory", font=("Arial", 24, "bold"))
title_label.pack(pady=20)

search_entry = ctk.CTkEntry(master=app, placeholder_text="Enter a name or number to search...", width=350, height=40,
                            corner_radius=8)
search_entry.pack(pady=10)

search_button = ctk.CTkButton(master=app, text="Find a contact", width=150, height=40, corner_radius=8,
                              font=("Arial", 14, "bold"), fg_color="#1f6aa5", hover_color="#144870",
                              command=search_contact)
search_button.pack(pady=10)

contacts_frame = ctk.CTkScrollableFrame(
    master=app,
    width=350,
    height=250,
    corner_radius=8,
    label_text=f"Contact list ({len(contacts)})",
    label_font=("Arial", 12, "bold")
)
contacts_frame.pack(pady=20)

btn_frame = ctk.CTkFrame(master=app, fg_color="transparent")
btn_frame.pack(pady=10)

add_contact_button = ctk.CTkButton(
    master=btn_frame,
    text="Add contact",
    width=170,
    height=40,
    corner_radius=8,
    fg_color="#2cb67d",
    hover_color="#1e8557",
    font=("Arial", 14, "bold"),
    command=open_add_contact_window
)
add_contact_button.pack(side="left", padx=5)


def open_favorites_window():
    fav_window = ctk.CTkToplevel(app)
    fav_window.title("Favorites")
    fav_window.geometry("400x450")
    fav_window.resizable(False, False)
    fav_window.attributes("-topmost", True)

    title_label = ctk.CTkLabel(master=fav_window, text="⭐ Favorite Contacts", font=("Arial", 20, "bold"))
    title_label.pack(pady=15)

    fav_entry = ctk.CTkEntry(master=fav_window, placeholder_text="Type name from list to add...", width=250)
    fav_entry.pack(pady=5)

    fav_scroll = ctk.CTkScrollableFrame(master=fav_window, width=320, height=200, corner_radius=8)
    fav_scroll.pack(pady=15)

    def refresh_fav_list():
        for widget in fav_scroll.winfo_children():
            widget.destroy()

        if not favorites:
            empty_lbl = ctk.CTkLabel(master=fav_scroll, text="Favorites list is empty", font=("Arial", 14, "italic"), text_color="gray")
            empty_lbl.pack(pady=20)
            return

        for name in sorted(favorites):
            if name in contacts:
                f_row = ctk.CTkFrame(master=fav_scroll, fg_color="transparent")
                f_row.pack(fill="x", padx=5, pady=3)

                lbl = ctk.CTkLabel(master=f_row, text=f"⭐ {name}: {contacts[name]}", font=("Arial", 14), anchor="w")
                lbl.pack(side="left", fill="x", expand=True, padx=5)

                def remove_fav(n=name):
                    favorites.remove(n)
                    save_favorites(favorites)
                    refresh_fav_list()
                    show_all_contacts()

                rem_btn = ctk.CTkButton(master=f_row, text="🗑️", width=30, height=25, fg_color="#e55039", hover_color="#b83b26", font=("Arial", 10), command=remove_fav)
                rem_btn.pack(side="right", padx=5)

    def add_to_fav():
        query = fav_entry.get().strip().lower()
        if not query:
            return

        matches = [name for name in contacts if query in name.lower() and name not in favorites]

        if not matches:
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="No new matches found!", placeholder_text_color="red")
            return

        if len(matches) == 1:
            name_to_add = matches[0]

            confirm_window = ctk.CTkToplevel(fav_window)
            confirm_window.title("Confirm")
            confirm_window.geometry("280x130")
            confirm_window.resizable(False, False)
            confirm_window.attributes("-topmost", True)

            lbl = ctk.CTkLabel(master=confirm_window, text=f"Add '{name_to_add}' to favorites?", font=("Arial", 14))
            lbl.pack(pady=15)

            c_frame = ctk.CTkFrame(master=confirm_window, fg_color="transparent")
            c_frame.pack()

            def confirm_add():
                favorites.append(name_to_add)
                save_favorites(favorites)
                fav_entry.delete(0, "end")
                fav_entry.configure(placeholder_text="Type name from list to add...", placeholder_text_color="gray")
                refresh_fav_list()
                show_all_contacts()
                confirm_window.destroy()

            y_btn = ctk.CTkButton(master=c_frame, text="Yes", width=80, fg_color="#2cb67d", hover_color="#1e8557", command=confirm_add)
            y_btn.pack(side="left", padx=10)
            n_btn = ctk.CTkButton(master=c_frame, text="No", width=80, fg_color="gray", hover_color="#555555", command=confirm_window.destroy)
            n_btn.pack(side="left", padx=10)
        else:
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="Multiple found! Be more specific.", placeholder_text_color="yellow")

    add_fav_btn = ctk.CTkButton(master=fav_window, text="Add to favorites", width=150, height=30, fg_color="#1f6aa5", command=add_to_fav)
    add_fav_btn.pack(pady=5)

    refresh_fav_list()

fav_button = ctk.CTkButton(
    master=btn_frame,
    text="Favorites",
    width=170,
    height=40,
    corner_radius=8,
    fg_color="#1f6aa5",
    hover_color="#144870",
    font=("Arial", 14, "bold"),
    command=open_favorites_window
)
fav_button.pack(side="left", padx=5)

show_all_contacts()
app.mainloop()

