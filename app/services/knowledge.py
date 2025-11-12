from app import prompt_hub, llm_hub
from app.services import supabase as db
from langfuse import Langfuse, observe
import uuid
from datetime import datetime

@observe(name="knowledge_generation_llm_call")
def generate_kn(group_members: list):
    # get_prompt now returns (template_str, config)
    template_str, prompt_config = prompt_hub.get_prompt("KN_generator")

    # Render prompt with group member data
    rendered_prompt = prompt_hub.render_prompt(
        template_str,
        INPUT_DATA=group_members,
    )

    # Extract model/temperature from config following your working pattern
    model_name = None
    temperature = 0.7
    top_p = 1

    if prompt_config:
        model_name = prompt_config.get("model", model_name)
        temperature = float(prompt_config.get("tempreature", temperature))

    if not model_name:
        raise ValueError("Prompt config missing 'model' for KN_generator prompt")

    response = llm_hub.generate_nvidia(
        rendered_prompt,
        model=model_name,
        temperature=temperature,
        top_p=top_p,
    )

    return response

@observe(name="knowledge_summary_llm_call")
def generate_kn_summary(kn_data: dict):
    # get_prompt now returns (template_str, config)
    template_str, prompt_config = prompt_hub.get_prompt("KN_Summerise")

    # Render prompt with KN graph/subgraph JSON
    rendered_prompt = prompt_hub.render_prompt(
        template_str,
        GRAPH_SUBGRAPH_JSON=str(kn_data),
    )

    model_name = None
    temperature = 0.7
    top_p = 1

    if prompt_config:
        model_name = prompt_config.get("model", model_name)
        temperature = float(prompt_config.get("tempreature", temperature))

    if not model_name:
        raise ValueError("Prompt config missing 'model' for KN_Summerise prompt")

    response = llm_hub.generate_nvidia(
        rendered_prompt,
        model=model_name,
        temperature=temperature,
        top_p=top_p,
    )

    return response
