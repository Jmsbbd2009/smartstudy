import json
from dataclasses import replace
import httpx
import pytest
from fastapi import HTTPException
from app.ai import huggingface
from app.ai.provider import TutorAnswer


def transport(monkeypatch, responses):
    settings = replace(
        huggingface.settings,
        hf_token="test-only-token",
        hf_model="Qwen/test",
        hf_guard_model="meta-llama/Llama-Guard-test",
    )
    monkeypatch.setattr(huggingface, "settings", settings)
    requests = []
    client_type = httpx.Client

    def handler(request):
        requests.append(json.loads(request.content))
        value = responses.pop(0)
        return httpx.Response(
            value if isinstance(value, int) else 200,
            json={}
            if isinstance(value, int)
            else {"choices": [{"message": {"content": value}}], "model": "test-model"},
        )

    monkeypatch.setattr(
        huggingface.httpx, "Client", lambda **kwargs: client_type(transport=httpx.MockTransport(handler))
    )
    return requests


def test_hf_structured_tutor_has_input_and_output_moderation(monkeypatch):
    requests = transport(
        monkeypatch,
        [
            "safe",
            json.dumps(
                {
                    "explanation": "Ikki va ikki — to‘rt.",
                    "hints": ["Barmoqlarda sanang"],
                    "practice": ["1+2?"],
                }
            ),
            "safe",
        ],
    )
    answer = huggingface.HuggingFaceProvider().structured("2+2?", TutorAnswer, "Teach arithmetic")
    assert len(requests) == 3 and answer._provider_model == "test-model"
    assert requests[1]["response_format"]["json_schema"]["strict"] is True
    assert "test-only-token" not in json.dumps(requests)


def test_hf_unsafe_input_never_reaches_tutor(monkeypatch):
    requests = transport(monkeypatch, ["unsafe\nS1"])
    with pytest.raises(HTTPException) as error:
        huggingface.HuggingFaceProvider().structured("unsafe content", TutorAnswer, "Teach")
    assert error.value.status_code == 422 and len(requests) == 1


def test_hf_payment_failure_never_returns_fake_ai(monkeypatch):
    transport(monkeypatch, [402])
    with pytest.raises(HTTPException) as error:
        huggingface.HuggingFaceProvider().structured("2+2?", TutorAnswer, "Teach")
    assert error.value.status_code == 503 and "test-only-token" not in str(error.value.detail)
