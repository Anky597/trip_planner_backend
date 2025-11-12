from app import prompt_hub, llm_hub
from langfuse import observe

@observe(name="plan_generation_llm_call")
def generate_plan(kn_summary: dict, raw_data: dict):
    template_str, prompt_config = prompt_hub.get_prompt("base_level_planner")

    rendered_prompt = prompt_hub.render_prompt(
        template_str,
        USER_PROFILE_SUMMARY=kn_summary,
        CITY_ACTIVITY_RESULTS=raw_data.get("short_trip"),
        SHORT_TRIP_OPTIONS=raw_data.get("long_trip"),
    )

    model_name = "gemini-2.5-pro"
    temperature = 0.3
    top_p = 1

    if prompt_config:
        model_name = prompt_config.get("model", model_name)
        if prompt_config.get("tempreature") is not None:
            temperature = float(prompt_config["tempreature"])

    if not model_name:
        raise ValueError("Prompt config missing 'model' for base_level_planner prompt.")

    return llm_hub.generate_google(
        rendered_prompt,
        model=model_name,
        temperature=temperature,
        top_p=top_p,
    )
