contacts = {
    "Ivan": "+79991112233",
    "Anna": "+79994445566"
}
while True:
    print("\n1. Find a contact.\n 2. Add a contact.\n 3. Show all.\n 4. Exit.")
    action = int(input("Select action: "))
    if action == 1:
        if action == 1:
            name = input("Enter a name to search: ")
            if name in contacts:
                print(f"Phone number: {contacts[name]}")
            else:
                print("Contact not found.")
    if action == 2:
        name_user = input("Enter name:")
        number = input("Enter number:")
        contacts[name_user] = number
        print("Successfully!")
    if action == 3:
        for name, phone in contacts.items():
            print(f"{name}: {phone}")
    if action == 4:
        break

