import json
from dataclasses import replace
import httpx
import pytest
from fastapi import HTTPException
from app.ai import hosted
from app.ai.provider import TutorAnswer


def configure(monkeypatch, responses):
    config = replace(
        hosted.settings,
        groq_key="groq-test-private",
        deepseek_key="deepseek-test-private",
        groq_model="openai/gpt-oss-120b",
        groq_guard_model="openai/gpt-oss-safeguard-20b",
    )
    monkeypatch.setattr(hosted, "settings", config)
    requests = []
    client = httpx.Client

    def handler(request):
        requests.append(request)
        value = responses.pop(0)
        return httpx.Response(
            value if isinstance(value, int) else 200,
            json={}
            if isinstance(value, int)
            else {"choices": [{"message": {"content": json.dumps(value)}}], "model": "test-live-format"},
        )

    monkeypatch.setattr(
        hosted.httpx, "Client", lambda **kwargs: client(transport=httpx.MockTransport(handler))
    )
    return requests


ANSWER = {
    "explanation": "Ikki bilan ikki to‘rt bo‘ladi.",
    "hints": ["Ikki juftni birlashtiring."],
    "practice": ["3+1?"],
}
SAFE = {"safe": True, "categories": []}


def test_groq_validates_structured_output_between_two_moderation_checks(monkeypatch):
    requests = configure(monkeypatch, [SAFE, ANSWER, SAFE])
    answer = hosted.HostedProvider("groq").structured("2+2?", TutorAnswer, "Teach")
    assert len(requests) == 3 and answer._provider_model == "groq:test-live-format"
    body = json.loads(requests[1].content)
    assert body["response_format"]["json_schema"]["strict"]
    assert body["response_format"]["json_schema"]["schema"]["required"] == [
        "explanation",
        "hints",
        "practice",
    ]


def test_deepseek_never_receives_groq_key_and_json_is_locally_validated(monkeypatch):
    requests = configure(monkeypatch, [SAFE, ANSWER, SAFE])
    answer = hosted.HostedProvider("deepseek").structured("2+2?", TutorAnswer, "Teach")
    assert answer.explanation and len(requests) == 3
    assert (
        requests[0].url.host == "api.groq.com"
        and requests[0].headers["Authorization"] == "Bearer groq-test-private"
    )
    assert (
        requests[1].url.host == "api.deepseek.com"
        and requests[1].headers["Authorization"] == "Bearer deepseek-test-private"
    )
    assert json.loads(requests[1].content)["response_format"] == {"type": "json_object"}


def test_unsafe_or_unavailable_guard_cannot_be_skipped(monkeypatch):
    requests = configure(monkeypatch, [{"safe": False, "categories": ["personal_data"]}])
    with pytest.raises(HTTPException) as error:
        hosted.HostedProvider("groq").structured("request", TutorAnswer, "Teach")
    assert error.value.status_code == 422 and len(requests) == 1
