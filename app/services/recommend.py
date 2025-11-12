from app import prompt_hub, llm_hub
from langfuse import observe
from datetime import datetime, timedelta
import asyncio

async def generate_recommendations(kn_summary: dict, destination: str):
    time_now = datetime.now()

    city_params = {
        "city": destination,
        "travel_profile": [time_now, time_now + timedelta(days=1)],
    }

    wide_params = {
        "city": destination,
        "travel_profile": [time_now, time_now + timedelta(days=3)],
        "radius": "100-200 km",
        "budget_per_person": "INR 5K - 10K",
    }

    # get_prompt returns (template_str, config); assumed fast/sync.
    city_template, city_config = prompt_hub.get_prompt("spot_finder")

    city_rendered = prompt_hub.render_prompt(
        city_template,
        USER_PROFILE_SUMMARY=kn_summary,
        DESTINATION_CONTEXT=city_params,
    )

    city_model = None
    city_temperature = 0.7

    if city_config:
        city_model = city_config.get("model", city_model)
        city_temperature = float(city_config.get("tempreature", city_temperature))

    if not city_model:
        raise ValueError("Prompt config missing 'model' for spot_finder prompt")

    loop = asyncio.get_running_loop()

    @observe(name="city_recommendations_llm_call")
    def _gen_city():
        return llm_hub.generate_google(
            city_rendered,
            model=city_model,
            temperature=city_temperature,
            top_p=1,
        )

    city_recs = await loop.run_in_executor(None, _gen_city)

    wide_template, wide_config = prompt_hub.get_prompt("Serach_retrival")

    wide_rendered = prompt_hub.render_prompt(
        wide_template,
        USER_PROFILE_SUMMARY=kn_summary,
        DESTINATION_CONTEXT=wide_params,
    )

    wide_model = None
    wide_temperature = 0.7

    if wide_config:
        wide_model = wide_config.get("model", wide_model)
        wide_temperature = float(wide_config.get("tempreature", wide_temperature))

    if not wide_model:
        raise ValueError("Prompt config missing 'model' for Serach_retrival prompt")

    @observe(name="wide_recommendations_llm_call")
    def _gen_wide():
        return llm_hub.generate_google(
            wide_rendered,
            model=wide_model,
            temperature=wide_temperature,
            top_p=1,
        )

    wide_recs = await loop.run_in_executor(None, _gen_wide)

    return {
        "short_trip": city_recs,
        "long_trip": wide_recs,
    }
