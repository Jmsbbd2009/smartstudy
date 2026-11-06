"""Actual application transport probe; public arithmetic only."""

import json
from pathlib import Path
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.ai.hosted import HostedProvider
from app.ai.provider import TutorAnswer


def main():
    report = {}
    observations = []
    original_client = httpx.Client

    def observe(response):
        response.read()
        record = {"host": response.request.url.host, "status": response.status_code}
        try:
            data = response.json()
            if response.status_code >= 400:
                record["error_code"] = data.get("error", {}).get("code")
                message = str(data.get("error", {}).get("message", ""))[:500]
                for secret in (settings.groq_key, settings.deepseek_key):
                    if secret:
                        message = message.replace(secret, "[redacted]")
                record["reason"] = message
            else:
                record["finish_reason"] = data.get("choices", [{}])[0].get("finish_reason")
        except (ValueError, IndexError, KeyError):
            pass
        observations.append(record)

    from app.ai import hosted

    hosted.httpx.Client = lambda **kw: original_client(event_hooks={"response": [observe]}, **kw)

    with httpx.Client(timeout=20) as client:
        try:
            response = client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": "Bearer " + settings.groq_key},
            )
            report["models_http_status"] = response.status_code
            if response.status_code == 200:
                report["available_model_ids"] = [m["id"] for m in response.json()["data"]]
        except httpx.HTTPError:
            report["models_status"] = "transport_unavailable"
    try:
        result = HostedProvider("groq").structured(
            "2+2 ni o‘zbek tilida sodda tushuntiring.",
            TutorAnswer,
            "Teach arithmetic with hints and practice in Uzbek Latin. Return only the required JSON.",
        )
        report["pipeline"] = "passed"
        report["model"] = result._provider_model
    except HTTPException as error:
        report["pipeline"] = "unavailable"
        report["pipeline_http_status"] = error.status_code
    report["observations"] = observations
    hosted.httpx.Client = original_client
    Path("/tmp/ssc03-toolchain/groq-probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
