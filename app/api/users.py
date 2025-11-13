from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import UserCreate, UserResponse, UserInfoResponse, GroupInfo, PlanResponse
from app.services import supabase as db
from app import prompt_hub, llm_hub
from langfuse import Langfuse
import uuid
from datetime import datetime
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    logger.info("create_user: start email=%s name=%s", user.email, user.name)
    with prompt_hub.langfuse.trace(name="user_signup_journey", user_id=user.email) as trace:
        existing_user = db.get_user_by_email(user.email)
        if existing_user:
            logger.warning("create_user: user exists email=%s", user.email)
            raise HTTPException(status_code=400, detail="User already exists")

        template_str, prompt_config = prompt_hub.get_prompt("user_intrest")

        rendered_prompt = prompt_hub.render_prompt(
            template_str,
            USER_RESPONSES=user.user_answer,
        )

        model_name = None
        temperature = 0.7
        top_p = 1

        if prompt_config:
            model_name = prompt_config.get("model", model_name)
            temperature = float(prompt_config.get("tempreature", temperature))

        if not model_name:
            raise HTTPException(
                status_code=500,
                detail="Prompt config missing 'model' for user_intrest prompt."
            )

        response = llm_hub.generate_openai(
            rendered_prompt,
            model=model_name,
            temperature=temperature,
            top_p=top_p,
        )

        persona = {
            "traits": response.get("top_traits"),
            "score": response.get("factor_scores")
        }

        user_data = {
            "id": str(uuid.uuid4()),
            "email": user.email,
            "name": user.name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "persona_traits": persona,
            "ai_summary": response.get("profile_summary")
        }

        db.insert_user(user_data)
        logger.info("create_user: success id=%s email=%s", user_data["id"], user.email)
        return user_data


@router.get("/users/info", response_model=UserInfoResponse)
async def get_user_info(email: str = Query(..., description="User email address")):
    logger.info("get_user_info: start email=%s", email)
    loop = asyncio.get_running_loop()

    user = await loop.run_in_executor(None, db.get_user_by_email, email)
    if not user:
        logger.warning("get_user_info: user not found email=%s", email)
        raise HTTPException(status_code=404, detail="User not found")

    user_groups = await loop.run_in_executor(None, db.get_user_groups, user["id"])

    groups_info = []
    for group in user_groups:
        group_id = group["id"]

        members = await loop.run_in_executor(None, db.get_group_members, group_id)
        member_details = []
        # Defensive: ensure role exists (default to "member")
        for member in members:
            member_user = await loop.run_in_executor(None, db.get_user_by_id, member["user_id"])
            if member_user:
                member_details.append({
                    "id": member_user["id"],
                    "email": member_user["email"],
                    "name": member_user["name"],
                    "role": member.get("role", "member"),
                    "persona_traits": member_user.get("persona_traits"),
                    "ai_summary": member_user.get("ai_summary")
                })

        group_plans = await loop.run_in_executor(None, db.get_group_plans, group_id)

        # KN summary normalization (if backend stored an array, pick the last one)
        kn_summary_raw = group.get("ai_group_kn_summary")
        if isinstance(kn_summary_raw, list) and kn_summary_raw:
            kn_summary_value = kn_summary_raw[-1]
        else:
            kn_summary_value = kn_summary_raw

        group_info = GroupInfo(
            id=group_id,
            name=group["name"],
            destination=group["destination"],
            creator_id=group["creator_id"],
            members=member_details,
            plans=group_plans
        )
        # Note: GroupInfo no longer includes ai_group_kn_summary in the schema.
        # We still compute it above to avoid future errors in case of internal usage.
        groups_info.append(group_info)

    logger.info("get_user_info: success email=%s groups=%d", email, len(groups_info))
    return UserInfoResponse(user=user, groups=groups_info)
