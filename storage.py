import streamlit as st
from supabase_client import supabase

# =====================================================
# IDEAS
# =====================================================

def get_all():
    response = supabase.table("ideas").select("*").execute()
    return response.data or []


def add_idea(idea):
    supabase.table("ideas").insert(idea).execute()


def update_idea(idea_id, updated_fields):
    supabase.table("ideas") \
        .update(updated_fields) \
        .eq("id", idea_id) \
        .execute()


# =====================================================
# USERS / PERMISSIONS
# =====================================================

def load_permissions():
    response = supabase.table("users").select("*").execute()
    return response.data or []


def add_user(email, role):
    supabase.table("users").insert({
        "email": email,
        "role": role
    }).execute()


def update_role(email, new_role):
    supabase.table("users") \
        .update({"role": new_role}) \
        .eq("email", email) \
        .execute()


def delete_user(email):
    supabase.table("users") \
        .delete() \
        .eq("email", email) \
        .execute()
