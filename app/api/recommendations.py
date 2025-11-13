from fastapi import APIRouter, HTTPException
from app.models.schemas import RecommendationsResponse
from app.services import supabase as db
from app.services import recommend
from app import prompt_hub
import asyncio
import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/groups/{group_id}/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(group_id: str):
    logger.info("get_recommendations: start group_id=%s", group_id)
    with prompt_hub.langfuse.trace(name="recommendation_plan_journey", metadata={"group_id": group_id}) as trace:
        loop = asyncio.get_running_loop()

        group = await loop.run_in_executor(None, db.get_group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        if not group.get("ai_group_kn_summary"):
            raise HTTPException(status_code=400, detail="Group processing not complete")

        try:
            recommendations = await recommend.generate_recommendations(
                group["ai_group_kn_summary"],
                group["destination"],
            )
            logger.info("get_recommendations: success group_id=%s", group_id)
            return recommendations
        except Exception as e:
            logger.exception("get_recommendations: fallback due to error group_id=%s", group_id)
            # Fallback: return a lightweight, deterministic recommendation payload
            # so the user flow isn't blocked during MVP demos (e.g., free tier/model errors).
            today = datetime.date.today()
            dummy = {
                "user_id": "User_001",
                "base_city": group.get("destination") or "Bangalore",
                "date_range": [
                    str(today),
                    str(today + datetime.timedelta(days=3)),
                ],
                "search_radius_km": 200,
                "short_trip_destinations": [
                    {
                        "option_variant": "Option A – Nature & Scenic Retreat",
                        "destination_name": "Nandi Hills",
                        "distance_from_base_km": "60",
                        "travel_time": "1.5 - 2 hours by car",
                        "trip_length_days": 2,
                        "key_highlights": [
                            "Sunrise trek and panoramic views from the hilltop",
                            "Paragliding and cycling options",
                            "Visit Tipu's Drop and Bhoga Nandeeshwara Temple",
                        ],
                        "accommodation_notes": "Budget guesthouses to mid-range resorts available nearby.",
                        "estimated_cost_per_person": "INR 5,000 - 8,000",
                        "transportation_options": ["drive", "bus", "train"],
                        "weather_during_trip": "Pleasant and cool (typical mid-season).",
                        "source": {
                            "title": "51 Places To Visit Near Bangalore Within 200 kms",
                            "url": "https://example.com/nandi-hills",
                            "snippet": "Nandi Hills blends historical charm with quick outdoor escapes.",
                        },
                    },
                    {
                        "option_variant": "Option B – Cultural & Heritage Destination",
                        "destination_name": "Mysore",
                        "distance_from_base_km": "145",
                        "travel_time": "3 - 4 hours by car/train",
                        "trip_length_days": 2,
                        "key_highlights": [
                            "Mysore Palace illumination",
                            "Devaraja Market walk",
                            "Chamundi Hills & St. Philomena's Church",
                        ],
                        "accommodation_notes": "City hotels and boutique heritage stays available.",
                        "estimated_cost_per_person": "INR 6,000 - 10,000",
                        "transportation_options": ["drive", "bus", "train"],
                        "weather_during_trip": "Pleasant and moderate.",
                        "source": {
                            "title": "Places to Visit Near Bangalore for 2 Days",
                            "url": "https://example.com/mysore",
                            "snippet": "The cultural capital with grand palaces and lively markets.",
                        },
                    },
                    {
                        "option_variant": "Option C – Adventure & Experiential",
                        "destination_name": "Ramanagara",
                        "distance_from_base_km": "50",
                        "travel_time": "1 - 1.5 hours by car",
                        "trip_length_days": 2,
                        "key_highlights": [
                            "Rock climbing and rappelling on granite hills",
                            "Trekking rugged trails",
                            "Zip-lining, cave exploration at adventure camps",
                        ],
                        "accommodation_notes": "Adventure camps, nature resorts, and basic guesthouses.",
                        "estimated_cost_per_person": "INR 5,500 - 8,500",
                        "transportation_options": ["drive", "bus", "train"],
                        "weather_during_trip": "Pleasant and dry; ideal for outdoor activities.",
                        "source": {
                            "title": "40 Places to Visit near Bangalore within 200 Kms",
                            "url": "https://example.com/ramanagara",
                            "snippet": "Adventure paradise near Bangalore with rugged trails.",
                        },
                    },
                ],
            }
            # Package into the expected RecommendationsResponse shape
            return {
                "short_trip": dummy,
                "long_trip": dummy,  # reuse for MVP; planner expects both keys present
            }
