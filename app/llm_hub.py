import json
import re
from openai import OpenAI
from google import genai
from google.genai.types import (
    Tool,
    GenerateContentConfig,
    GoogleSearch,
)
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
from langfuse import Langfuse, observe
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

GoogleGenAIInstrumentor().instrument()


def clean_llm_json(text: str) -> str:
    if not text:
        return ""

    # Match ```json ... ``` or ``` ... ``` (non-greedy inner)
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    return text.strip()



def generate_openai(prompt: str, model: str, **kwargs):
    """Generate content using OpenAI API."""
    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.OPENAI_BASE_URL
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a JSON-only API. "
                    "Read the instructions below and respond with a SINGLE valid JSON object. "
                    "Do not include explanations, markdown, or code fences. "
                    "If you reference lists or nested data, include them as proper JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        **kwargs,
    )

    raw_content = response.choices[0].message.content or ""
    output = clean_llm_json(raw_content)

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise ValueError(
            f"LLM did not return valid JSON. Raw output was:\n{raw_content!r}"
        )



def generate_nvidia(prompt: str, model: str, **kwargs):
    """Generate content using NVIDIA API."""
    client = OpenAI(
        api_key=settings.nvidia_api_key,
        base_url=settings.NVIDIA_BASE_URL
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Follow the system prompt and complete the task according"}
        ],
        **kwargs
    )
    output = clean_llm_json(response.choices[0].message.content)
    return json.loads(output)



def generate_google(prompt: str, model: str, **kwargs):
    """
    Generate content using Google GenAI with grounding (Google Search + URL Context).

    This function uses the google-genai SDK with Tool objects for grounding.
    It processes grounding metadata and adds inline citations to the response.
    """
    client = genai.Client(api_key=settings.google_api_key)

    # Define tools using Tool objects with GoogleSearch
    tools = [
        Tool(google_search=GoogleSearch()),
    ]

    # Create generation config with tools
    config = GenerateContentConfig(
        temperature=kwargs.get('temperature', 1),
        top_p=kwargs.get('top_p', 1),
        tools=tools
    )

    # Generate content with grounding
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )
    
    if not response.candidates:
        raise ValueError("Google GenAI returned no candidates")
    else:
        candidate = response.candidates[0]
        text = candidate.content.parts[0].text
        cleaned_text = clean_llm_json(text) or ""
        parsed_json = json.loads(cleaned_text)

        return parsed_json

