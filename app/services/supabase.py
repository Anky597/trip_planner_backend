from supabase import create_client, Client
from app.core.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def get_user_by_email(email: str):
    response = supabase.table("users").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None

def insert_user(user_data: dict):
    response = supabase.table("users").insert(user_data).execute()
    return response.data

def get_group(group_id: str):
    response = supabase.table("groups").select("*").eq("id", group_id).execute()
    return response.data[0] if response.data else None


def get_group_by_name(group_name: str):
    response = supabase.table("groups").select("*").eq("name", group_name).execute()
    return response.data[0] if response.data else None

def insert_group(group_data: dict):
    response = supabase.table("groups").insert(group_data).execute()
    return response.data

def get_group_member(group_id: str, user_id: str):
    response = supabase.table("group_members").select("*").eq("group_id", group_id).eq("user_id", user_id).execute()
    return response.data[0] if response.data else None

def insert_group_member(member_data: dict):
    response = supabase.table("group_members").insert(member_data).execute()
    return response.data

def get_group_members(group_id: str):
    response = supabase.table("group_members").select("user_id").eq("group_id", group_id).execute()
    return response.data

def get_users_by_ids(user_ids: list):
    response = supabase.table("users").select("persona_traits, ai_summary").in_("id", user_ids).execute()
    return response.data

def insert_knowledge_graph(kg_data: dict):
    response = supabase.table("knowledge_graphs").insert(kg_data).execute()
    return response.data

def update_group_kn_summary(group_id: str, summary: dict):
    response = supabase.table("groups").update({"ai_group_kn_summary": summary}).eq("id", group_id).execute()
    return response.data

def insert_trip_plan(plan_data: dict):
    response = supabase.table("trip_plans").insert(plan_data).execute()
    return response.data


def get_user_groups(user_id: str):
    response = supabase.table("group_members").select("group_id").eq("user_id", user_id).execute()
    group_ids = [item["group_id"] for item in response.data]

    if not group_ids:
        return []

    response = supabase.table("groups").select("*").in_("id", group_ids).execute()
    return response.data


def get_user_by_id(user_id: str):
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None


def get_group_plans(group_id: str):
    response = supabase.table("trip_plans").select("*").eq("group_id", group_id).execute()
    return response.data
