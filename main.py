import json
import os

file_name = "contacts.json"

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        contacts = json.load(file)
else:
    contacts = {
        "Ivan": "+79991112233",
        "Anna": "+79994445566"
    }

while True:
    print("1. Find a contact.\n2. Add a contact.\n3. Show all.\n4. Delete contact:\n5. Edit contact.\n6. Exit")
    action = int(input("Select action: "))
    if action == 1:
        name = input("Enter a name to search: ")

        name_check = name.title() # check for capital letters

        if name_check in contacts:
            print(f"Phone number: {contacts[name_check]}")
        else:
            print("Contact not found.")

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

    if action == 3:
        for name, phone in contacts.items():
            print(f"{name}: {phone}")

    if action == 4:
        name = input("Enter a name to delete: ")
        name_check = name.title()

        if name_check in contacts:
            del contacts[name_check] #delete
            print(f"Contact {name_check} successfully deleted!")
        else:
            print("Contact not found.")

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
        else:
            print("Contact not found.")

    if action == 6:
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(contacts, file, ensure_ascii=False, indent=4)
        print("Contacts saved.")
        break

