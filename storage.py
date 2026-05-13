# =========================================================
# STORAGE.PY
# COMPLETE COPY-PASTE VERSION
# =========================================================

import json
import os

# =========================================================
# IDEA STORAGE
# =========================================================
IDEA_FILE = "ideas.json"


def load_data():

    if not os.path.exists(IDEA_FILE):

        with open(IDEA_FILE, "w") as f:
            json.dump([], f)

    with open(IDEA_FILE, "r") as f:

        return json.load(f)


def save_data(data):

    with open(IDEA_FILE, "w") as f:

        json.dump(data, f, indent=4)


def add_idea(item):

    data = load_data()

    data.append(item)

    save_data(data)


def get_all():

    return load_data()


def update_idea(idea_id, updates):

    data = load_data()

    for item in data:

        if item["id"] == idea_id:

            item.update(updates)

    save_data(data)


# =========================================================
# PERMISSION STORAGE
# =========================================================
PERMISSION_FILE = "permissions.json"


def load_permissions():

    if not os.path.exists(PERMISSION_FILE):

        default_users = [

            {
                "email": "ravi.manoharan@alten-india.com",
                "role": "super user"
            }

        ]

        with open(PERMISSION_FILE, "w") as f:

            json.dump(default_users, f, indent=4)

    with open(PERMISSION_FILE, "r") as f:

        return json.load(f)


def save_permissions(data):

    with open(PERMISSION_FILE, "w") as f:

        json.dump(data, f, indent=4)


def add_user(email, role):

    data = load_permissions()

    exists = False

    for x in data:

        if x["email"] == email:
            exists = True

    if not exists:

        data.append({
            "email": email,
            "role": role
        })

        save_permissions(data)


def delete_user(email):

    data = load_permissions()

    data = [
        x for x in data
        if x["email"] != email
    ]

    save_permissions(data)


def update_role(email, role):

    data = load_permissions()

    for x in data:

        if x["email"] == email:

            x["role"] = role

    save_permissions(data)
