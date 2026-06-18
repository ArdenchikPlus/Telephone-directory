import customtkinter as ctk

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
    hover_color="#144870"
)
search_button.pack(pady=10)

app.mainloop()
