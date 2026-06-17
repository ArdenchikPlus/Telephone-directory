import json
import os

file_name = "contacts.json"
fav_file_name = "favorites.json"

def save_contacts(data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def save_favorites(data):
    with open(fav_file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        contacts = json.load(file)
else:
    contacts = {"Ivan": "+79991112233", "Anna": "+79994445566"}

if os.path.exists(fav_file_name):
    with open(fav_file_name, "r", encoding="utf-8") as file:
        favorites = json.load(file)
else:
    favorites = []


while True:
    print(f"""
    MAIN MENU (Total Contacts: {len(contacts)})
    1. Find a contact.
    2. Add a contact.
    3. Show all.
    4. Delete contact.
    5. Edit contact.
    6. Favorites.
    7. Exit.""".strip())

    action = input("\nSelect action: ").strip()

    if not action.isdigit() or action not in "1234567":
        print("Invalid input! Please enter a number from 1 to 7.")
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
            print("No contacts found matching your query.")
        input("\nPress Enter to continue...")

    if action == 2:
        name_user = input("Enter name: ")
        name_check = name_user.title()

        while True:
            number = input("Enter number: ").strip()
            if number.isdigit():
                break
            else:
                print("Invalid input! Please enter digits only (no letters or spaces inside).")
        contacts[name_check] = number
        print("Successfully added!")

        save_contacts(contacts)
        input("\nPress Enter to continue...")

    if action == 3:
        print(f"\n--- Total Contacts: {len(contacts)} ---")
        for name, phone in sorted(contacts.items()):
            print(f"{name}: {phone}")
        input("\nPress Enter to continue...")

    if action == 4:
        name = input("Enter a name to delete: ")
        name_check = name.title()

        if name_check in contacts:
            del contacts[name_check]
            print(f"Contact {name_check} successfully deleted!")

            save_contacts(contacts)
        else:
            print("Contact not found.")
        input("\nPress Enter to continue...")

    if action == 5:
        name_edit = input("Enter the name of the person you want to change the number for: ")
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
            save_contacts(contacts)
        else:
            print("Contact not found.")
        input("\nPress Enter to continue...")

    if action == 6:
        while True:
            print(f"""
\nFAVORITES MENU (Saved: {len(favorites)})
1. Show favorites
2. Add to favorites
3. Remove from favorites
4. Back to main menu""".strip())

            fav_action = input("\nSelect favorite action: ").strip()
            if fav_action not in ["1", "2", "3", "4"]:
                print("Invalid input! Choose 1-4.")
                continue

            if fav_action == "1":
                print("\nYour Favorite Contacts")
                if not favorites:
                    print("Your favorites list is empty.")
                else:
                    for name in sorted(favorites):
                        if name in contacts:
                            print(f"{name}: {contacts[name]}")
                        else:
                            print(f"{name}: [Contact deleted from main phonebook]")
                input("\nPress Enter to continue...")

            elif fav_action == "2":
                query = input("Enter part of the name to add to favorites: ").strip().lower()
                matches = [name for name in contacts if query in name.lower()]

                if not matches:
                    print("No contacts found in phonebook matching your query.")
                elif len(matches) == 1:
                    name_to_add = matches[0]
                    confirm = input(
                        f"Found 1 contact: '{name_to_add}'. Do you want to add it? (y/n): ").strip().lower()
                    if confirm == 'y':
                        if name_to_add in favorites:
                            print(f"{name_to_add} is already in your favorites!")
                        else:
                            favorites.append(name_to_add)
                            print(f"{name_to_add} added to favorites")
                            save_favorites(favorites)
                    else:
                        print("Canceled.")
                else:
                    print("\nMultiple contacts found. Please enter the exact name from this list:")
                    for match in matches:
                        print(f" - {match}")

                    exact_name = input("\nEnter exact name: ").strip().title()
                    if exact_name in matches:
                        if exact_name in favorites:
                            print(f"{exact_name} is already in your favorites!")
                        else:
                            favorites.append(exact_name)
                            print(f"{exact_name} added to favorites")
                            save_favorites(favorites)
                    else:
                        print("Name does not match the list.")

                input("\nPress Enter to continue...")

            elif fav_action == "3":
                query = input("Enter part of the name to remove from favorites: ").strip().lower()
                matches = [name for name in favorites if query in name.lower()]

                if not matches:
                    print("No contacts found in favorites matching your query.")
                elif len(matches) == 1:
                    name_to_remove = matches[0]
                    confirm = input(
                        f"Found 1 contact: '{name_to_remove}'. Do you want to remove it? (y/n): ").strip().lower()
                    if confirm == 'y':
                        favorites.remove(name_to_remove)
                        print(f"{name_to_remove} removed from favorites.")
                        save_favorites(favorites)
                    else:
                        print("Canceled.")
                else:
                    print("\nMultiple favorites found. Please enter the exact name to remove:")
                    for match in matches:
                        print(f" - {match}")

                    exact_name = input("\nEnter exact name: ").strip().title()
                    if exact_name in matches:
                        favorites.remove(exact_name)
                        print(f"{exact_name} removed from favorites.")
                        save_favorites(favorites)
                    else:
                        print("Name does not match the list.")

                input("\nPress Enter to continue...")

            elif fav_action == "4":
                break

    if action == 7:
        print("Goodbye!")
        break
