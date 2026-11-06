"""Live provider qualification on public test facts, never real student records."""

import json
import sys
import httpx
from pathlib import Path
from types import SimpleNamespace
from fastapi import HTTPException
from app.ai.provider import provider
from app.schemas.reading import LessonContent, PracticePlan
from app.services.reading import validate_grounding


def main():
    facts = [
        "Water freezes at zero degrees Celsius.",
        "Plants use sunlight to make food.",
        "Earth travels around the Sun once each year.",
    ]
    observations = []
    original_client = httpx.Client

    def observe(response):
        response.read()
        item = {"status": response.status_code}
        try:
            data = response.json()
            if response.status_code >= 400:
                item["error_code"] = data.get("error", {}).get("code")
                reason = str(data.get("error", {}).get("message", ""))[:800]
                from app.core.config import settings

                for secret in (settings.groq_key, settings.deepseek_key, settings.hf_token):
                    if secret:
                        reason = reason.replace(secret, "[redacted]")
                item["reason"] = reason
            else:
                item["finish_reason"] = data.get("choices", [{}])[0].get("finish_reason")
        except (ValueError, IndexError, KeyError):
            pass
        observations.append(item)

    from app.ai import hosted

    hosted.httpx.Client = lambda **kw: original_client(event_hooks={"response": [observe]}, **kw)
    report = {"student_data_sent": False, "publication": "adult validation still required"}
    try:
        lesson = provider.structured(
            "\n".join(f"[PAGE {i + 1}] {fact}" for i, fact in enumerate(facts)),
            LessonContent,
            "Create an Uzbek Latin school lesson using only the supplied facts. Use exactly 3 questions and 3 concepts. Each question and concept must cite its exact source_page and exact verbatim source_quote (8-600 chars). Use IDs made of lowercase ASCII letters. Return the specified JSON only. The answer keys require adult validation before publication.",
        )
        validate_grounding(
            lesson, [SimpleNamespace(page_number=i + 1, text=fact) for i, fact in enumerate(facts)]
        )
        report["book_lesson"] = {
            "passed": True,
            "concepts": len(lesson.concepts),
            "questions": len(lesson.questions),
            "source_quotes": "validated",
            "model": lesson._provider_model,
        }
    except HTTPException as error:
        report["book_lesson"] = {"passed": False, "status": error.status_code}
    if "--book-only" not in sys.argv:
        try:
            plan = provider.structured(
                "Create two short optional multiplication revision exercises with breaks. No real student data.",
                PracticePlan,
                "Support learning in Uzbek Latin. Use at most 2 short tasks and no punishment or device-policy instructions. Return only the specified JSON.",
            )
            report["practice_plan"] = {
                "passed": True,
                "tasks": len(plan.tasks),
                "model": plan._provider_model,
                "executed_on_students": False,
            }
        except HTTPException as error:
            report["practice_plan"] = {"passed": False, "status": error.status_code}
    hosted.httpx.Client = original_client
    report["observations"] = observations
    Path("/tmp/ssc03-toolchain/learning-probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
