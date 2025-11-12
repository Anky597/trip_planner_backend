from fastapi import APIRouter, HTTPException
from app.models.schemas import PlanCreate, PlanResponse, GeneratePlanRequest, ErrorResponse
from app.services import supabase as db
from app.services import plan
from app import prompt_hub
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/groups/{group_id}/plan", response_model=PlanResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}})
async def create_plan(group_id: str, plan_data: PlanCreate):
    with prompt_hub.langfuse.trace(name="plan_generation_journey", metadata={"group_id": group_id}) as trace:
        group = db.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail={"code": "GROUP_NOT_FOUND", "message": "Group not found"})

        if not group.get("ai_group_kn_summary"):
            raise HTTPException(status_code=400, detail={"code": "KN_NOT_READY", "message": "Group processing not complete"})

        generated_plan = plan.generate_plan(group["ai_group_kn_summary"], plan_data.raw_data)

        if not isinstance(generated_plan, dict) or "plan_options" not in generated_plan:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "LLM_BAD_RESPONSE",
                    "message": "Plan generator did not return expected plan_options structure",
                    "details": generated_plan,
                },
            )

        plan_record = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "plan_json": generated_plan,
            "summary_caption": "Generated multi-option plan",
            "estimated_cost_per_person": None,
            "created_at": datetime.now().isoformat(),
        }

        db.insert_trip_plan(plan_record)
        return plan_record

@router.post("/plans/by-group-name", response_model=PlanResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}})
async def create_plan_by_group_name(payload: GeneratePlanRequest):
    with prompt_hub.langfuse.trace(name="plan_generation_journey_by_name", metadata={"group_name": payload.group_name}) as trace:
        group = db.get_group_by_name(payload.group_name)
        if not group:
            raise HTTPException(status_code=404, detail={"code": "GROUP_NOT_FOUND", "message": "Group not found"})

        if not group.get("ai_group_kn_summary"):
            raise HTTPException(status_code=400, detail={"code": "KN_NOT_READY", "message": "Group processing not complete"})

        generated_plan = plan.generate_plan(group["ai_group_kn_summary"], payload.raw_data)

        if not isinstance(generated_plan, dict) or "plan_options" not in generated_plan:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "LLM_BAD_RESPONSE",
                    "message": "Plan generator did not return expected plan_options structure",
                    "details": generated_plan,
                },
            )

        plan_record = {
            "id": str(uuid.uuid4()),
            "group_id": group["id"],
            "plan_json": generated_plan,
            "summary_caption": "Generated multi-option plan",
            "estimated_cost_per_person": None,
            "created_at": datetime.now().isoformat(),
        }

        db.insert_trip_plan(plan_record)
        return plan_record
