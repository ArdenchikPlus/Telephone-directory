contacts = {
    "Ivan": "+79991112233",
    "Anna": "+79994445566"
}
while True:
    print("1. Find a contact.\n 2. Add a contact.\n 3. Show all.\n 4. Exit.")
    action = int(input("Select action: "))
    if action == 1:
        name = input("Enter a name to search: ")

        name_check = name.title() # check for capital letters

        if name_check in contacts:
            print(f"Phone number: {contacts[name_check]}")
        else:
            print("Contact not found.")

    if action == 2:
        name_user = input("Enter name:")
        name_check = name_user.title()
        number = input("Enter number:")
        contacts[name_check] = number
        print("Successfully!")

    if action == 3:
        for name, phone in contacts.items():
            print(f"{name}: {phone}")

    if action == 4:
        break

