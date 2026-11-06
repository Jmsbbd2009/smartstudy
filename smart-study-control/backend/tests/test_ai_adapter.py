from dataclasses import replace
import httpx
import pytest
from fastapi import HTTPException
from app.ai import provider as module


def setup_provider(monkeypatch, handler):
    monkeypatch.setattr(
        module,
        "settings",
        replace(
            module.settings,
            ai_url="https://ai.example.test/v1",
            ai_key="local-test-only",
            ai_model="test-model",
            moderation_url="https://ai.example.test/moderations",
        ),
    )
    original = httpx.Client
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(module.httpx, "Client", lambda **kw: original(transport=transport, **kw))
    return module.OpenAICompatibleProvider()


def test_provider_requires_input_and_output_moderation_and_strict_schema(monkeypatch):
    calls = []

    def handler(request):
        import json

        body = json.loads(request.content)
        calls.append(request.url.path)
        if request.url.path.endswith("moderations"):
            return httpx.Response(200, json={"results": [{"flagged": False}]})
        schema = body["response_format"]["json_schema"]["schema"]
        assert set(schema["required"]) == set(schema["properties"])
        assert schema["additionalProperties"] is False
        return httpx.Response(
            200,
            json={
                "model": "pinned-test-version",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "correct": 1,
                                    "total": 2,
                                    "confidence": 0.4,
                                    "feedback": "O‘qituvchi bilan ko‘rib chiqing",
                                    "human_required": True,
                                }
                            )
                        }
                    }
                ],
            },
        )

    result = setup_provider(monkeypatch, handler).structured("Schoolwork", module.Evaluation, "School review")
    assert result.human_required and result.confidence == 0.4
    assert result._provider_model == "pinned-test-version"
    assert calls == ["/moderations", "/v1/chat/completions", "/moderations"]


def test_flagged_input_never_reaches_model(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"results": [{"flagged": True}]})

    with pytest.raises(HTTPException) as exc:
        setup_provider(monkeypatch, handler).structured("Unsafe material", module.TutorAnswer, "Tutor")
    assert exc.value.status_code == 422
    assert calls == ["/moderations"]


def test_malformed_ai_json_fails_closed(monkeypatch):
    def handler(request):
        if request.url.path.endswith("moderations"):
            return httpx.Response(200, json={"results": [{"flagged": False}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "unverified answer"}}]})

    with pytest.raises(HTTPException) as exc:
        setup_provider(monkeypatch, handler).structured("Math", module.TutorAnswer, "Tutor")
    assert exc.value.status_code == 503
