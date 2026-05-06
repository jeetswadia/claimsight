"""LLM router — abstracts away provider details from agents.

Implements the two-tier strategy from ADR-0002:
    cheap → Groq Llama-3.3-70B (free tier, fast, good enough for specialists)
    smart → Claude Sonnet 4 (paid, used by adjudicator and critic only)

Agents request a tier and get back a unified `LLMResponse`. This concentrates
provider-specific code, retry logic, and cost tracking in one place.

Usage:
    from src.agents.llm_router import call_llm

    result = call_llm(
        tier="cheap",
        system="You are a medical necessity reviewer.",
        user="Is a knee MRI medically necessary for chronic knee pain?",
    )
    print(result.text)
    print(f"Cost: ${result.cost_usd:.4f}, Latency: {result.latency_ms}ms")
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Literal

import httpx
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

Tier = Literal["cheap", "smart"]


@dataclass
class LLMResponse:
    text: str
    tier: Tier
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


# Pricing (USD per 1M tokens). Update when providers change pricing.
PRICING = {
    "groq-llama-3.3-70b": {"input": 0.00, "output": 0.00},  # Free tier
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def _call_groq(system: str, user: str, max_tokens: int) -> LLMResponse:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    started = time.perf_counter()
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    latency_ms = int((time.perf_counter() - started) * 1000)

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)

    return LLMResponse(
        text=text,
        tier="cheap",
        model="groq-llama-3.3-70b",
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_usd=_estimate_cost("groq-llama-3.3-70b", in_tok, out_tok),
        latency_ms=latency_ms,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def _call_anthropic(system: str, user: str, max_tokens: int) -> LLMResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    started = time.perf_counter()
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    latency_ms = int((time.perf_counter() - started) * 1000)

    text = "".join(b["text"] for b in data["content"] if b["type"] == "text")
    usage = data.get("usage", {})
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)

    return LLMResponse(
        text=text,
        tier="smart",
        model="claude-sonnet-4",
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_usd=_estimate_cost("claude-sonnet-4", in_tok, out_tok),
        latency_ms=latency_ms,
    )


def _mock_response(system: str, user: str) -> LLMResponse:
    """Deterministic mock used when no API keys are present.

    The demo (and CI) need to run without provider credentials. The mock
    inspects the user prompt for keywords to return plausibly-shaped JSON
    matching what the medical-necessity agent expects. This keeps the entire
    pipeline exercisable end-to-end with zero setup.

    The mock's responses are intentionally aligned with the demo scenarios so
    the user sees a believable adjudication flow even before adding API keys.
    """
    import json

    p = user.lower()
    if "73721" in p or ("mri" in p and "knee" in p):
        payload = {
            "decision": "approve",
            "confidence": 0.88,
            "rationale": (
                "Patient has documented osteoarthritis (M17.11) with prior "
                "physical therapy and office visits over a 6+ week period, "
                "consistent with conservative therapy failure. MRI is supported "
                "by the guideline criteria. (Mocked — set GROQ_API_KEY for real LLM.)"
            ),
            "cited_sections": [
                "conservative management (including physical therapy and NSAIDs) over a period of at least 6 weeks has failed",
                "advanced imaging such as MRI is generally reserved for cases where",
            ],
        }
    elif "30400" in p or "rhinoplasty" in p or "z41.1" in p:
        payload = {
            "decision": "deny",
            "confidence": 0.95,
            "rationale": (
                "Procedure coded with Z41.1 (Encounter for cosmetic surgery) as "
                "the primary diagnosis with no functional impairment documented. "
                "Coverage exclusion for cosmetic procedures applies. "
                "(Mocked — set GROQ_API_KEY for real LLM.)"
            ),
            "cited_sections": [
                "Cosmetic procedures performed solely to improve appearance, without functional impairment, are not covered",
                "ICD-10 code Z41.1 (Encounter for cosmetic surgery) is explicitly excluded from coverage",
            ],
        }
    elif "95810" in p or "polysomnography" in p or "sleep" in p:
        payload = {
            "decision": "route",
            "confidence": 0.55,
            "rationale": (
                "ICD-10 R53.83 alone is insufficient to establish medical "
                "necessity for polysomnography. No documented sleep-disorder "
                "symptoms or risk factors in the available context. Recommend "
                "human review for additional clinical documentation. "
                "(Mocked — set GROQ_API_KEY for real LLM.)"
            ),
            "cited_sections": [
                "ICD-10 R53.83 (Other fatigue) alone is not typically sufficient to establish medical necessity for polysomnography",
                "Additional clinical documentation supporting suspicion of a specific sleep disorder is generally required",
            ],
        }
    else:
        payload = {
            "decision": "route",
            "confidence": 0.5,
            "rationale": (
                "Insufficient context for an automated decision. "
                "(Mocked — set GROQ_API_KEY for a real LLM call.)"
            ),
            "cited_sections": [],
        }

    return LLMResponse(
        text=json.dumps(payload, indent=2),
        tier="cheap",
        model="mock-llm",
        input_tokens=len(system + user) // 4,
        output_tokens=len(json.dumps(payload)) // 4,
        cost_usd=0.0,
        latency_ms=15,
    )


def call_llm(*, tier: Tier, system: str, user: str, max_tokens: int = 1024) -> LLMResponse:
    """Route an LLM call based on tier. See ADR-0002 for the strategy.

    If the relevant API key is missing, falls back to a deterministic mock so
    development, demos, and CI are never blocked on credentials. The mock is
    clearly marked in the response text so it's never confused for a real call.
    """
    if tier == "cheap":
        if not os.getenv("GROQ_API_KEY"):
            return _mock_response(system, user)
        return _call_groq(system, user, max_tokens)
    if tier == "smart":
        if not os.getenv("ANTHROPIC_API_KEY"):
            # Smart tier falls back to cheap (Groq) before mock — better quality
            # than the mock if a Groq key is available
            if os.getenv("GROQ_API_KEY"):
                return _call_groq(system, user, max_tokens)
            return _mock_response(system, user)
        return _call_anthropic(system, user, max_tokens)
    raise ValueError(f"Unknown tier: {tier}")
