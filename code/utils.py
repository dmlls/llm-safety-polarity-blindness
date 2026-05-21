"""Utilities."""

import json
import re

import litellm
import yaml
from litellm import (
    APIConnectionError,
    BadRequestError,
    UnsupportedParamsError,
    completion,
)

# Disable LiteLLM debug information.
litellm.suppress_debug_info = True


def load_config(config_path: str | None = None) -> dict:
    if config_path is None:
        config_path = "config.yml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def completion_without_reasoning(model, messages):
    reasoning_levels = ["none", "minimal", "low"]
    kwargs = {
        "model": model,
        "messages": messages,
    }
    if model.startswith("ollama"):
        kwargs["api_base"] = load_config().get("ollama_base_url")
    # Different models support different levels of reasoning. We try from lower
    # to higher reasoning.
    response = None
    for reasoning_effort in reasoning_levels:
        kwargs["reasoning_effort"] = reasoning_effort
        try:
            response = completion(**kwargs)
        except (
            APIConnectionError,
            BadRequestError,
            UnsupportedParamsError,
            ValueError,
        ):
            # Last try: run without specifying reasoning effort.
            if reasoning_effort == reasoning_levels[-1]:
                kwargs.pop("reasoning_effort", None)
                response = completion(**kwargs)
        if response is not None:
            break
    return response


def inference(model, messages):
    kwargs = {
        "model": model,
        "messages": messages,
    }
    config = load_config()
    if any("kimi-k2.5" in model for model in config.get("judge_models")):
        kwargs["order"] = [
            "io-net/int4",
            "chutes/int4",
            "inceptron/int4",
            "deepinfra",
            "siliconflow/int4",
            "atlas-cloud/int4",
        ]

    if model.startswith("ollama"):
        kwargs["api_base"] = config.get("ollama_base_url")
    response = completion(**kwargs)
    return response.choices[0].message.content


def inference_without_reasoning(model, messages):
    response = completion_without_reasoning(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


def parse_json(string: str) -> dict | None:
    if string:
        extracted_json = re.findall(r"\{[^{]*?\}", string, re.DOTALL)
        for extracted in extracted_json:
            try:
                result = json.loads(extracted)
                return {
                    "harm": result["harm"],
                    "disclaimer": result["disclaimer"],
                    "refusal": result["refusal"],
                }
            except (
                json.JSONDecodeError,
                AttributeError,
                ValueError,
                TypeError,
                KeyError,
            ):
                pass
    raise ValueError("Could not extract JSON from string")
