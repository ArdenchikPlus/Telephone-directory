import customtkinter as ctk
import json
import os

def save_contacts(data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


file_name = "contacts.json"

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        contacts = json.load(file)
else:
    contacts = {
        "Ivan": "+79991112233",
        "Anna": "+79994445566"
    }

def show_all_contacts():

    for widget in contacts_frame.winfo_children():
        widget.destroy()

    for name, phone in sorted(contacts.items()):

        contact_label = ctk.CTkLabel(
            master=contacts_frame,
            text=f"👤 {name}: {phone}",
            font=("Arial", 14),
            anchor="w"
        )

        contact_label.pack(fill="x", padx=10, pady=5)

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
            contact_label = ctk.CTkLabel(
                master=contacts_frame,
                text=f"👤 {name}: {phone}",
                font=("Arial", 14),
                anchor="w"
            )
            contact_label.pack(fill="x", padx=10, pady=5)
            found = True

    if not found:
        no_result_label = ctk.CTkLabel(
            master=contacts_frame,
            text="Nothing found",
            font=("Arial", 14, "italic"),
            text_color="gray"
        )
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
        show_all_contacts()
        add_window.destroy()

    error_label = ctk.CTkLabel(master=add_window, text="", font=("Arial", 12))
    error_label.pack(pady=5)

    save_button = ctk.CTkButton(
        master=add_window,
        text="Save",
        width=150,
        height=35,
        corner_radius=8,
        fg_color="#2cb67d",
        hover_color="#1e8557",
        command=save_new_contact
    )
    save_button.pack(pady=10)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Phonebook v1.0")
app.geometry("500x600")
app.resizable(False, False)

title_label = ctk.CTkLabel(
    master=app,
    text="Telephone directory",
    font=("Arial", 24, "bold")
)
title_label.pack(pady=20)

search_entry = ctk.CTkEntry(
    master=app,
    placeholder_text="Enter a name or number to search...",
    width=350,
    height=40,
    corner_radius=8
)
search_entry.pack(pady=10)

search_button = ctk.CTkButton(
    master=app,
    text="Find a contact",
    width=150,
    height=40,
    corner_radius=8,
    font=("Arial", 14, "bold"),
    fg_color="#1f6aa5",
    hover_color="#144870",
    command=search_contact
)
search_button.pack(pady=10)


contacts_frame = ctk.CTkScrollableFrame(
    master=app,
    width=350,
    height=250,
    corner_radius=8,
    label_text="Contact list",
    label_font=("Arial", 12, "bold")
)
contacts_frame.pack(pady=20)

add_contact_button = ctk.CTkButton(
    master=app,
    text="Add a contact",
    width=350,
    height=40,
    corner_radius=8,
    fg_color="#2cb67d",
    hover_color="#1e8557",
    font=("Arial", 14, "bold"),
    command=open_add_contact_window
)
add_contact_button.pack(pady=10)

show_all_contacts()

app.mainloop()
