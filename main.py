import json
import os
from xml.etree.ElementTree import indent

file_name = "contacts.json"

def save_contacts():
    with open (file_name,'w',encoding = 'utf-8') as file:
        json.dump(contacts,file,ensure_ascii=False,indent = 4)
if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        contacts = json.load(file)
else:
    contacts = {
        "Ivan": "+79991112233",
        "Anna": "+79994445566"
    }


while True:
    print("""
    1. Find a contact.
    2. Add a contact.
    3. Show all.
    4. Delete contact.
    5. Edit contact.
    6. Exit
    """.strip())

    action = input("Select action: ").strip()

    if not action.isdigit() or action not in "123456":
        print("Invalid input! Please enter a number from 1 to 6.")
        continue

    action = int(action)

    if action == 1:

        search_query = input("Enter name or phone number to search: ").strip().lower()
        found = False

        print("\n--- Search Results ---")

        for name, phone in contacts.items():
            name_lower = name.lower()
            phone_lower = phone.lower()

            if search_query in name_lower or search_query in phone_lower:
                print(f"{name}: {phone}")
                found = True

        if not found:
            print("Contacts not found.")

        input("\nPress Enter to continue...")

    if action == 2:
        name_user = input("Enter name: ")
        name_check = name_user.title()

        while True:
            number = input("Enter number:").strip()
            if number.isdigit():
                break
            else:
                print("Invalid input! Please enter digits only (no letters or spaces inside).")
        contacts[name_check] = number
        print("Successfully added!")
        save_contacts()
        input("\nPress Enter to continue...")

    if action == 3:
        for name, phone in contacts.items():
            print(f"{name}: {phone}")
        input("\nPress Enter to continue...")

    if action == 4:
        name = input("Enter a name to delete: ")
        name_check = name.title()

        if name_check in contacts:
            del contacts[name_check] #delete
            print(f"Contact {name_check} successfully deleted!")
            save_contacts()
        else:
            print("Contact not found.")
        input("\nPress Enter to continue...")

    if action == 5:
        name_edit = input("Enter the name of the person you want to change the number for:")
        name_check = name_edit.title()

        if name_check in contacts:
            print(f"Current phone number for {name_check}: {contacts[name_check]}")

            while True:
                new_number = input("Enter new number: ").strip()
                if new_number.isdigit():
                    break
                else:
                    print("Invalid input! Please enter digits only.")

            contacts[name_check] = new_number
            print(f"Contact {name_check} successfully updated!")
            save_contacts()
        else:
            print("Contact not found.")
        input("\nPress Enter to continue...")

    if action == 6:
        print("See you!")
        break

