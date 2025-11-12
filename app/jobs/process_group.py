from app.services import supabase as db
from app.services import knowledge
from langfuse import observe
import uuid
from datetime import datetime
import asyncio

@observe
async def process_group(group_id: str):
    # NOTE: Supabase Python client is sync; run blocking calls in thread pool
    loop = asyncio.get_running_loop()

    members = await loop.run_in_executor(None, db.get_group_members, group_id)
    if not members:
        return

    user_ids = [m["user_id"] for m in members]

    users = await loop.run_in_executor(None, db.get_users_by_ids, user_ids)
    group_members = [
        {"persona_traits": u["persona_traits"], "ai_summary": u["ai_summary"]}
        for u in users
    ]

    # knowledge.* assumed pure/sync and cheap enough to run inline
    kn_data = knowledge.generate_kn(group_members)

    kg_record = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "graph_json": kn_data,
        "updated_at": datetime.now().isoformat(),
    }

    await loop.run_in_executor(None, db.insert_knowledge_graph, kg_record)

    kn_summary = knowledge.generate_kn_summary(kn_data)
    await loop.run_in_executor(None, db.update_group_kn_summary, group_id, kn_summary)

@observe
async def refresh_kn(group_id: str):
    await process_group(group_id)
