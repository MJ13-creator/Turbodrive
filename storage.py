import json
import os
from datetime import datetime

# =========================================================
# IDEA STORAGE
# =========================================================

IDEA_FILE = "ideas.json"

# =========================================================
# USER ACCESS STORAGE
# =========================================================

USER_FILE = "users.json"

# =========================================================
# IDEAS
# =========================================================

def load():

    if not os.path.exists(IDEA_FILE):
        return []

    with open(IDEA_FILE, "r") as f:
        return json.load(f)

def save(data):

    with open(IDEA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_idea(item):

    data = load()

    item["id"] = len(data) + 1

    item["status"] = "New Idea"

    item["created_at"] = datetime.now().isoformat()

    data.append(item)

    save(data)

def update_idea(id_, updates):

    data = load()

    for i in data:

        if i["id"] == id_:

            for k, v in updates.items():
                i[k] = v

    save(data)

def get_all():

    return load()

# =========================================================
# USERS
# =========================================================

def load_users():

    if not os.path.exists(USER_FILE):

        with open(USER_FILE, "w") as f:
            json.dump([], f)

    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):

    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def add_user(user):

    users = load_users()

    users.append(user)

    save_users(users)

def delete_user(email):

    users = load_users()

    users = [
        u for u in users
        if u["email"].lower() != email.lower()
    ]

    save_users(users)

def update_user(email, updates):

    users = load_users()

    for user in users:

        if user["email"].lower() == email.lower():

            for k, v in updates.items():
                user[k] = v

    save_users(users)

def get_user(email):

    users = load_users()

    for user in users:

        if user["email"].lower() == email.lower():
            return user

    return None