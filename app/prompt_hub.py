import os
from langfuse import Langfuse, observe
from jinja2 import Template
from app.core.config import settings
from contextlib import nullcontext

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
)

# Compatibility: some code uses `langfuse.trace(...)` as a context manager (JS-style API).
# The Python SDK v3 does not expose this; provide a no-op context manager to avoid runtime errors.
if not hasattr(langfuse, "trace"):
    def _trace_stub(*args, **kwargs):
        return nullcontext()
    setattr(langfuse, "trace", _trace_stub)


def get_prompt(label: str):
    """
    Fetch a prompt from Langfuse by label and normalize it to (template_str, config).
    """
    prompt_obj = langfuse.get_prompt(label , label="production")
    # For current Langfuse SDKs, prompt_obj.prompt is typically the template string.
    template_str = getattr(prompt_obj, "prompt", prompt_obj)
    config = getattr(prompt_obj, "config", None)
    return template_str, config

def render_prompt(template_str: str, **kwargs):
    template = Template(template_str)
    return template.render(**kwargs)
