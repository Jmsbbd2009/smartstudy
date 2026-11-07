"""Disposable real HTTP integration; optional Playwright browser run, no external accounts."""

import json
import os
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
MODE = os.getenv("E2E_MODE", "dom")
if MODE not in ("dom", "browser"):
    raise SystemExit("E2E_MODE must be dom or browser")


def stop(process):
    if process.poll() is None:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait()


with tempfile.TemporaryDirectory(prefix="study-e2e-") as tmp:
    directory = Path(tmp)
    env = {
        **os.environ,
        "APP_ENV": "test",
        "JWT_SECRET": secrets.token_urlsafe(48),
        "DATABASE_URL": "sqlite:///" + str(directory / "e2e.db"),
        "UPLOAD_DIR": str(directory / "uploads"),
        "REDIS_URL": "",
        "CORS_ORIGINS": "http://127.0.0.1:4179",
        "VITE_API_URL": "http://127.0.0.1:8089/api/v1",
        "TEST_API_URL": "http://127.0.0.1:8089/api/v1",
        "TEST_UI_URL": "http://127.0.0.1:4179",
        "LIVE_E2E": "1",
        "DEBUG_PRINT_LIMIT": "1800",
        "TEST_ACCOUNT_PASSWORD": secrets.token_urlsafe(24),
        "AI_BASE_URL": "",
        "AI_API_KEY": "",
        "AI_MODEL": "",
        "AI_MODERATION_URL": "",
        "TEST_SCREENSHOT_DIR": str(directory),
        "TEST_RESULTS_JSON": str(directory / "results.json"),
        "TEST_ACCESS_RESULTS_JSON": str(directory / "access-results.json"),
        "TEST_BOOK_PDF": str(directory / "source.pdf"),
    }
    sys.path[:0] = [str(BACKEND), str(BACKEND / "tests")]
    from test_reading import make_pdf

    (directory / "source.pdf").write_bytes(make_pdf())
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env=env,
        check=True,
    )
    seed = """import os
from app.db.session import SessionLocal
from app.models.entities import User,Wallet,ParentLink,Consent
from app.security.auth import hasher
with SessionLocal.begin() as db:
    users=[]
    for role,name in [("PARENT","Test Parent"),("STUDENT","Test Child"),("TEACHER","Test Teacher"),("SUPER_ADMIN","Test Super")]:
        u=User(email=role.lower()+".e2e@example.test",name=name,role=role,password_hash=hasher.hash(os.environ["TEST_ACCOUNT_PASSWORD"]));db.add(u);db.flush();users.append(u)
    parent,child,teacher=users[:3]
    users[3].login="5551234567"
    db.add(Wallet(student_id=child.id));db.add(ParentLink(parent_id=parent.id,child_id=child.id));db.add(Consent(actor_id=parent.id,child_id=child.id,purpose="disposable_e2e_test",granted=True))
"""
    subprocess.run([sys.executable, "-c", seed], cwd=BACKEND, env=env, check=True)
    processes = []
    logs = []
    try:

        def launch(command, cwd, name):
            log = (directory / name).open("w")
            logs.append(log)
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=os.name == "posix",
            )
            processes.append(process)

        launch(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8089",
            ],
            BACKEND,
            "api.log",
        )
        urls = ["http://127.0.0.1:8089/health/ready"]
        if MODE == "browser":
            launch(
                ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "4179"],
                ROOT / "admin-web",
                "web.log",
            )
            urls.append("http://127.0.0.1:4179")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for url in urls:
            for _ in range(60):
                try:
                    with opener.open(url, timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.25)
            else:
                raise RuntimeError("Local test service did not start")
        command = (
            [os.getenv("CODEX_PRIMARY_RUNTIME_NODE", "node"), "tests/reading-e2e.mjs"]
            if MODE == "browser"
            else [
                "npm",
                "exec",
                "--",
                "vitest",
                "run",
                "src/app/reading-live.e2e.test.tsx",
                "src/app/access-live.e2e.test.tsx",
            ]
        )
        result = subprocess.run(command, cwd=ROOT / "admin-web", env=env)
        output = Path(os.getenv("E2E_OUTPUT_DIR", str(ROOT / "docs/test-results")))
        output.mkdir(parents=True, exist_ok=True)
        if result.returncode:
            print((directory / "api.log").read_text()[-4000:])
            raise SystemExit(result.returncode)
        summary = json.loads((directory / "results.json").read_text())
        (
            output / ("browser-e2e.json" if MODE == "browser" else "dom-live-e2e.json")
        ).write_text(json.dumps(summary, indent=2) + "\n")
        if (directory / "access-results.json").exists():
            shutil.copy2(
                directory / "access-results.json", output / "access-live-e2e.json"
            )
        # Screenshots remain temporary unless an internal diagnostic directory is explicit.
        if os.getenv("E2E_DIAGNOSTICS_DIR"):
            diagnostic = Path(os.environ["E2E_DIAGNOSTICS_DIR"])
            diagnostic.mkdir(parents=True, exist_ok=True)
            for image in directory.glob("*.png"):
                shutil.copy2(image, diagnostic / image.name)
    finally:
        for process in processes:
            stop(process)
        for log in logs:
            log.close()
