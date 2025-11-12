from fastapi import APIRouter, HTTPException
from app.models.schemas import GroupCreate, GroupResponse, MemberAdd, MemberResponse, GroupTraitsResponse, ErrorResponse
from app.services import supabase as db
from app.services import knowledge
from app import prompt_hub
import uuid
from datetime import datetime
import asyncio

router = APIRouter()

@router.post("/groups", response_model=GroupResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def create_group(group: GroupCreate):
    with prompt_hub.langfuse.trace(name="group_creation_journey") as trace:
        loop = asyncio.get_running_loop()
        creator = await loop.run_in_executor(None, db.get_user_by_email, group.creator_email)
        if not creator:
            raise HTTPException(status_code=404, detail={"code": "CREATOR_NOT_FOUND", "message": "Creator not found"})
        group_data = {
            "id": str(uuid.uuid4()),
            "name": group.group_name,
            "creator_id": creator["id"],
            "destination": group.destination,
            "created_at": datetime.now().isoformat(),
        }
        await loop.run_in_executor(None, db.insert_group, group_data)
        member_data = {
            "group_id": group_data["id"],
            "user_id": creator["id"],
            "role": "creator",
            "joined_at": datetime.now().isoformat(),
        }
        await loop.run_in_executor(None, db.insert_group_member, member_data)
        members = await loop.run_in_executor(None, db.get_group_members, group_data["id"])
        user_ids = [m["user_id"] for m in members]
        users = await loop.run_in_executor(None, db.get_users_by_ids, user_ids)
        group_members = [{"persona_traits": u["persona_traits"], "ai_summary": u["ai_summary"]} for u in users]
        kn_data = await loop.run_in_executor(None, knowledge.generate_kn, group_members)
        kg_record = {
            "id": str(uuid.uuid4()),
            "group_id": group_data["id"],
            "graph_json": kn_data,
            "updated_at": datetime.now().isoformat(),
        }
        await loop.run_in_executor(None, db.insert_knowledge_graph, kg_record)
        kn_summary = await loop.run_in_executor(None, knowledge.generate_kn_summary, kn_data)
        await loop.run_in_executor(None, db.update_group_kn_summary, group_data["id"], kn_summary)
        return group_data

@router.post("/groups/{group_id}/members", response_model=MemberResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def add_member(group_id: str, member: MemberAdd):
    with prompt_hub.langfuse.trace(name="group_member_add_journey") as trace:
        loop = asyncio.get_running_loop()
        user = await loop.run_in_executor(None, db.get_user_by_email, member.user_email)
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
        existing_member = await loop.run_in_executor(None, db.get_group_member, group_id, user["id"])
        if existing_member:
            raise HTTPException(status_code=400, detail={"code": "USER_ALREADY_IN_GROUP", "message": "User already in group"})
        member_data = {
            "group_id": group_id,
            "user_id": user["id"],
            "role": "member",
            "joined_at": datetime.now().isoformat(),
        }
        await loop.run_in_executor(None, db.insert_group_member, member_data)
        members = await loop.run_in_executor(None, db.get_group_members, group_id)
        user_ids = [m["user_id"] for m in members]
        users = await loop.run_in_executor(None, db.get_users_by_ids, user_ids)
        group_members = [{"persona_traits": u["persona_traits"], "ai_summary": u["ai_summary"]} for u in users]
        kn_data = await loop.run_in_executor(None, knowledge.generate_kn, group_members)
        kg_record = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "graph_json": kn_data,
            "updated_at": datetime.now().isoformat(),
        }
        await loop.run_in_executor(None, db.insert_knowledge_graph, kg_record)
        kn_summary = await loop.run_in_executor(None, knowledge.generate_kn_summary, kn_data)
        await loop.run_in_executor(None, db.update_group_kn_summary, group_id, kn_summary)
        return member_data

@router.get("/groups/{group_id}/traits", response_model=GroupTraitsResponse, responses={404: {"model": ErrorResponse}})
async def get_group_traits(group_id: str):
    loop = asyncio.get_running_loop()

    group = await loop.run_in_executor(None, db.get_group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail={"code": "GROUP_NOT_FOUND", "message": "Group not found"})

    members = await loop.run_in_executor(None, db.get_group_members, group_id)
    if not members:
        raise HTTPException(status_code=404, detail={"code": "NO_MEMBERS_FOUND", "message": "No members found"})

    user_ids = [m["user_id"] for m in members]
    users = await loop.run_in_executor(None, db.get_users_by_ids, user_ids)

    return {
        "group_id": group_id,
        "group_name": group["name"],
        "group_members": [{"persona_traits": u["persona_traits"], "ai_summary": u["ai_summary"]} for u in users]
    }

@router.post("/groups/{group_id}/process", responses={404: {"model": ErrorResponse}})
async def process_group_manually(group_id: str):
    with prompt_hub.langfuse.trace(name="manual_group_processing") as trace:
        loop = asyncio.get_running_loop()
        group = await loop.run_in_executor(None, db.get_group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail={"code": "GROUP_NOT_FOUND", "message": "Group not found"})
        members = await loop.run_in_executor(None, db.get_group_members, group_id)
        user_ids = [m["user_id"] for m in members]
        users = await loop.run_in_executor(None, db.get_users_by_ids, user_ids)
        group_members = [{"persona_traits": u["persona_traits"], "ai_summary": u["ai_summary"]} for u in users]
        kn_data = await loop.run_in_executor(None, knowledge.generate_kn, group_members)
        kg_record = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "graph_json": kn_data,
            "updated_at": datetime.now().isoformat(),
        }
        await loop.run_in_executor(None, db.insert_knowledge_graph, kg_record)
        kn_summary = await loop.run_in_executor(None, knowledge.generate_kn_summary, kn_data)
        await loop.run_in_executor(None, db.update_group_kn_summary, group_id, kn_summary)
        return {"message": "Processing completed"}
