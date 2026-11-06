"""Attended integration probe: public arithmetic only, no student data or secret output."""

import json
from pathlib import Path
import httpx
from app.core.config import settings
from app.ai.huggingface import HuggingFaceProvider
from app.ai.provider import TutorAnswer
from fastapi import HTTPException


def main():
    report = {"live_inference": False}
    with httpx.Client(timeout=45) as client:
        try:
            response = client.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": "Bearer " + settings.hf_token},
            )
            report["token_http_status"] = response.status_code
            report["token_accepted"] = response.status_code == 200
        except httpx.HTTPError:
            report["token_status"] = "transport_unavailable"
        try:
            response = client.post(
                "https://router.huggingface.co/v1/chat/completions",
                headers={"Authorization": "Bearer " + settings.hf_token},
                json={
                    "model": settings.hf_model,
                    "messages": [{"role": "user", "content": "What is 2+2? Answer in one short sentence."}],
                    "max_tokens": 32,
                },
            )
            report["text_http_status"] = response.status_code
            if response.status_code == 200:
                report["text_model_responded"] = bool(response.json().get("choices"))
        except httpx.HTTPError:
            report["text_status"] = "transport_unavailable"
    try:
        result = HuggingFaceProvider().structured(
            "2 + 2 ni sodda o‘zbek tilida tushuntiring.",
            TutorAnswer,
            "You are a supportive school tutor. Explain arithmetic in Uzbek Latin, with hints and practice.",
        )
        report["live_inference"] = True
        report["structured_pipeline"] = "validated"
        report["model"] = result._provider_model
    except HTTPException as exc:
        report["structured_pipeline"] = "unavailable"
        report["pipeline_http_status"] = exc.status_code
    path = Path("/tmp/ssc03-toolchain/hf-probe.json")
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
