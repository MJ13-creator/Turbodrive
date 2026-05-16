# =========================================================
# STORAGE.PY
# COMPLETE UPDATED COPY-PASTE VERSION
# =========================================================

import json
import os
import re

# =========================================================
# CLEAN FUNCTION
# =========================================================
def clean(x):

    if x is None:
        return ""

    x = str(x).replace("\u00a0", "")
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)

    return x


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

        data = json.load(f)

    # =====================================================
    # CLEAN ALL USERS
    # =====================================================
    cleaned_data = []

    for user in data:

        cleaned_data.append({

            "email": clean(user.get("email", "")),
            "role": clean(user.get("role", ""))

        })

    return cleaned_data


def save_permissions(data):

    with open(PERMISSION_FILE, "w") as f:

        json.dump(data, f, indent=4)


# =========================================================
# ADD USER
# =========================================================
def add_user(email, role):

    data = load_permissions()

    email = clean(email)
    role = clean(role)

    exists = False

    for x in data:

        if clean(x["email"]) == email:
            exists = True

    if not exists:

        data.append({

            "email": email,
            "role": role
        })

        save_permissions(data)


# =========================================================
# DELETE USER
# =========================================================
def delete_user(email):

    data = load_permissions()

    email = clean(email)

    data = [

        x for x in data
        if clean(x["email"]) != email
    ]

    save_permissions(data)


# =========================================================
# UPDATE ROLE
# =========================================================
def update_role(email, role):

    data = load_permissions()

    email = clean(email)
    role = clean(role)

    for x in data:

        if clean(x["email"]) == email:

            x["role"] = role

    save_permissions(data)
