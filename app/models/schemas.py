from pydantic import BaseModel
from typing import Dict, Any, Optional, Literal, List


class UserCreate(BaseModel):
    email: str
    name: str
    user_answer: Dict[str, Any]


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    persona_traits: Dict[str, Any]
    ai_summary: str


class GroupCreate(BaseModel):
    group_name: str
    destination: str
    creator_email: str


class GroupResponse(BaseModel):
    id: str
    name: str
    creator_id: str
    destination: str


class MemberAdd(BaseModel):
    user_email: str


class MemberResponse(BaseModel):
    group_id: str
    user_id: str
    role: str


class GroupTraitsResponse(BaseModel):
    group_id: str
    group_name: str
    group_members: list


class RecommendationsResponse(BaseModel):
    short_trip: Dict[str, Any]
    long_trip: Dict[str, Any]


class PlanCreate(BaseModel):
    raw_data: Dict[str, Any]


class PlanResponse(BaseModel):
    id: str
    group_id: str
    plan_json: Dict[str, Any]
    summary_caption: str
    estimated_cost_per_person: Optional[float]


class ErrorResponse(BaseModel):
    code: str
    message: str
    trace_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class JobType(str):
    PROCESS_GROUP_TRAITS = "PROCESS_GROUP_TRAITS"


class JobStatus(str):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobCreate(BaseModel):
    type: Literal["PROCESS_GROUP_TRAITS"]
    group_id: str


class JobResponse(BaseModel):
    id: str
    type: str
    group_id: str
    status: str
    error_message: Optional[str] = None


class GeneratePlanRequest(BaseModel):
    group_name: str
    raw_data: Dict[str, Any]


class GeneratePlanResponse(BaseModel):
    plan: PlanResponse


class GroupInfo(BaseModel):
    id: str
    name: str
    destination: str
    creator_id: str
    members: List[Dict[str, Any]]
    plans: List[PlanResponse]


class UserInfoResponse(BaseModel):
    user: UserResponse
    groups: List[GroupInfo]
