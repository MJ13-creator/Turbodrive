import requests
import json
import streamlit as st
import base64

TOKEN = st.secrets[GITHUB_TOKEN]
REPO = st.secrets[GITHUB_REPO]

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# =====================================================
# LOAD JSON FROM GITHUB
# =====================================================
def load_json(filename):

    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:

        content = response.json()["content"]

        decoded = base64.b64decode(content).decode("utf-8")

        return json.loads(decoded)

    return []

# =====================================================
# SAVE JSON TO GITHUB
# =====================================================
def save_json(filename, data):

    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"

    # Get SHA
    response = requests.get(url, headers=HEADERS)

    sha = response.json()["sha"]

    content = json.dumps(data, indent=4)

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": f"update {filename}",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, headers=HEADERS, json=payload)

# =====================================================
# IDEAS
# =====================================================
def get_all():

    return load_json("ideas.json")

def add_idea(idea):

    data = get_all()

    data.append(idea)

    save_json("ideas.json", data)

def update_idea(idea_id, updated_fields):

    data = get_all()

    for item in data:

        if item["id"] == idea_id:

            item.update(updated_fields)

    save_json("ideas.json", data)

# =====================================================
# USERS
# =====================================================
def load_permissions():

    return load_json("permissions.json")

def add_user(email, role):

    users = load_permissions()

    users.append({
        "email": email,
        "role": role
    })

    save_json("permissions.json", users)

def update_role(email, new_role):

    users = load_permissions()

    for user in users:

        if user["email"] == email:

            user["role"] = new_role

    save_json("permissions.json", users)

def delete_user(email):

    users = load_permissions()

    users = [
        u for u in users
        if u["email"] != email
    ]

    save_json("permissions.json", users)
