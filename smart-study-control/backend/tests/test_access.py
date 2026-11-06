import base64
import hashlib
import json
import secrets
from dataclasses import replace
import cbor2
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from app.models.entities import AuthChallenge


def setup_bot(monkeypatch):
    from app.api import access
    from app.integrations import telegram

    config = replace(
        access.settings,
        telegram_token="test-only-token",
        telegram_username="TestBot",
        telegram_webhook_secret="test-only-secret",
        passkey_rp_id="localhost",
        passkey_origin="http://localhost:5173",
    )
    monkeypatch.setattr(access, "settings", config)
    monkeypatch.setattr(telegram, "settings", config)
    sent = []
    monkeypatch.setattr(telegram.transport, "send", lambda chat, text: sent.append((chat, text)))
    return sent


def test_superadmin_creates_staff_and_requires_password_renewal(people):
    c, f, p = people
    root = p["super_admin5"]["headers"]
    body = {
        "login": "admin.school",
        "email": "admin.staff@example.test",
        "name": "Admin",
        "password": "Temporary-password-123",
        "role": "SCHOOL_ADMIN",
        "school_name": "School A",
    }
    assert c.post("/api/v1/staff", headers=p["teacher3"]["headers"], json=body).status_code == 403
    created = c.post("/api/v1/staff", headers=root, json=body)
    assert created.status_code == 201, created.text
    assert "password" not in created.json()
    login = c.post("/api/v1/auth/login", json={"email": "admin.school", "password": body["password"]}).json()
    assert login["user"]["must_change_password"]
    old = {"Authorization": "Bearer " + login["access_token"]}
    assert c.get("/api/v1/staff", headers=old).status_code == 403
    changed = c.post(
        "/api/v1/auth/password",
        headers=old,
        json={"current_password": body["password"], "new_password": "New-secure-password-456"},
    )
    assert changed.status_code == 200, changed.text
    assert not changed.json()["user"]["must_change_password"]
    assert c.get("/api/v1/staff", headers=old).status_code == 401
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}).status_code == 401
    teacher = {
        **body,
        "login": "teacher.school",
        "email": "teacher.staff@example.test",
        "role": "TEACHER",
        "school_id": created.json()["school_id"],
        "school_name": None,
    }
    assert c.post("/api/v1/staff", headers=root, json=teacher).status_code == 201
    assert len(c.get("/api/v1/notifications", headers=root).json()) == 2


def test_bootstrap_normalizes_login_and_never_replaces_password(context):
    from app.bootstrap import bootstrap

    c, f = context
    with f.begin() as db:
        assert bootstrap(db, "50 0773209", "unit-only-password-123")
    with f.begin() as db:
        assert not bootstrap(db, "500773209", "another-password-123")
    result = c.post("/api/v1/auth/login", json={"email": "50 0773209", "password": "unit-only-password-123"})
    assert result.status_code == 200 and result.json()["user"]["must_change_password"]


def linked(c, f, p, monkeypatch):
    sent = setup_bot(monkeypatch)
    headers = p["teacher3"]["headers"]
    start = c.post(
        "/api/v1/auth/telegram/link/start", headers=headers, json={"password": "Strong-password-123"}
    ).json()
    update = {
        "update_id": 100,
        "message": {
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "is_bot": False},
            "text": "/start " + start["deep_link"].split("start=")[1],
        },
    }
    assert c.post("/api/v1/telegram/webhook", json=update).status_code == 403
    assert (
        c.post(
            "/api/v1/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-only-secret"},
            json=update,
        ).status_code
        == 200
    )
    result = c.post(
        "/api/v1/auth/telegram/link/finish",
        headers=headers,
        json={
            "challenge_id": start["challenge_id"],
            "verifier": start["verifier"],
            "password": "Strong-password-123",
        },
    )
    assert result.status_code == 200, result.text
    return sent


def test_telegram_identity_binding_delivery_and_replay(people, monkeypatch):
    c, f, p = people
    sent = linked(c, f, p, monkeypatch)
    start = c.post(
        "/api/v1/auth/telegram/login/start", json={"login": p["teacher3"]["tokens"]["user"]["email"]}
    ).json()
    state = start["deep_link"].split("start=")[1]
    update = {
        "update_id": 101,
        "message": {"chat": {"id": 999, "type": "private"}, "from": {"id": 999}, "text": "/start " + state},
    }
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-only-secret"}
    c.post("/api/v1/telegram/webhook", headers=headers, json=update)
    assert len(sent) == 1
    update["update_id"] = 102
    update["message"]["chat"]["id"] = 123456
    update["message"]["from"]["id"] = 123456
    for _ in range(2):
        c.post("/api/v1/telegram/webhook", headers=headers, json=update)
    assert len(sent) == 2
    code = sent[-1][1].split("kodi: ")[1][:6]
    proof = {"challenge_id": start["challenge_id"], "verifier": start["verifier"], "code": code}
    assert c.post("/api/v1/auth/telegram/login/finish", json=proof).status_code == 200
    assert c.post("/api/v1/auth/telegram/login/finish", json=proof).status_code == 401
    with f() as db:
        assert db.get(AuthChallenge, start["challenge_id"]).code_hash != code


def test_otp_bruteforce_counter_persists(people, monkeypatch):
    c, f, p = people
    linked(c, f, p, monkeypatch)
    start = c.post(
        "/api/v1/auth/telegram/login/start", json={"login": p["teacher3"]["tokens"]["user"]["email"]}
    ).json()
    for _ in range(6):
        assert (
            c.post(
                "/api/v1/auth/telegram/login/finish",
                json={"challenge_id": start["challenge_id"], "verifier": start["verifier"], "code": "000000"},
            ).status_code
            == 401
        )
    with f() as db:
        assert db.get(AuthChallenge, start["challenge_id"]).attempts == 5


def b64(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def key_registration(c, p):
    headers = p["teacher3"]["headers"]
    challenge = c.post(
        "/api/v1/auth/passkeys/register/options", headers=headers, json={"password": "Strong-password-123"}
    ).json()
    key = ec.generate_private_key(ec.SECP256R1())
    numbers = key.public_key().public_numbers()
    credential = secrets.token_bytes(32)
    cose = {1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32, "big"), -3: numbers.y.to_bytes(32, "big")}
    auth = (
        hashlib.sha256(b"localhost").digest()
        + bytes([0x45])
        + bytes(4)
        + bytes(16)
        + len(credential).to_bytes(2, "big")
        + credential
        + cbor2.dumps(cose)
    )
    client = json.dumps(
        {
            "type": "webauthn.create",
            "challenge": challenge["options"]["challenge"],
            "origin": "http://localhost:5173",
        }
    ).encode()
    response = {
        "id": b64(credential),
        "rawId": b64(credential),
        "type": "public-key",
        "response": {
            "clientDataJSON": b64(client),
            "attestationObject": b64(cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth})),
        },
        "clientExtensionResults": {},
    }
    result = c.post(
        "/api/v1/auth/passkeys/register/verify",
        headers=headers,
        json={
            "challenge_id": challenge["challenge_id"],
            "verifier": challenge["verifier"],
            "credential": response,
        },
    )
    assert result.status_code == 200, result.text
    return key, credential


def signed_assertion(key, credential, challenge, origin, flags):
    auth = hashlib.sha256(b"localhost").digest() + bytes([flags]) + (1).to_bytes(4, "big")
    client = json.dumps(
        {"type": "webauthn.get", "challenge": challenge["options"]["challenge"], "origin": origin}
    ).encode()
    signature = key.sign(auth + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
    return {
        "id": b64(credential),
        "rawId": b64(credential),
        "type": "public-key",
        "response": {
            "clientDataJSON": b64(client),
            "authenticatorData": b64(auth),
            "signature": b64(signature),
            "userHandle": None,
        },
        "clientExtensionResults": {},
    }


@pytest.mark.parametrize(
    "origin,flags,expected",
    [("http://localhost:5173", 5, 200), ("https://evil.example", 5, 401), ("http://localhost:5173", 1, 401)],
)
def test_passkey_cryptographic_signature_origin_uv_and_replay(people, monkeypatch, origin, flags, expected):
    c, f, p = people
    setup_bot(monkeypatch)
    key, credential = key_registration(c, p)
    challenge = c.post(
        "/api/v1/auth/passkeys/login/options", json={"login": p["teacher3"]["tokens"]["user"]["email"]}
    ).json()
    body = {
        "challenge_id": challenge["challenge_id"],
        "verifier": challenge["verifier"],
        "credential": signed_assertion(key, credential, challenge, origin, flags),
    }
    result = c.post("/api/v1/auth/passkeys/login/verify", json=body)
    assert result.status_code == expected, result.text
    if expected == 200:
        assert c.post("/api/v1/auth/passkeys/login/verify", json=body).status_code == 401


def test_school_admin_and_teacher_cannot_cross_school_staff_scope(people):
    c, f, p = people
    root = p["super_admin5"]["headers"]
    a = c.post(
        "/api/v1/staff",
        headers=root,
        json={
            "login": "admin.a",
            "email": "a.staff@example.test",
            "name": "A",
            "password": "Temporary-password-123",
            "role": "SCHOOL_ADMIN",
            "school_name": "School A",
        },
    ).json()
    b = c.post(
        "/api/v1/staff",
        headers=root,
        json={
            "login": "admin.b",
            "email": "b.staff@example.test",
            "name": "B",
            "password": "Temporary-password-123",
            "role": "SCHOOL_ADMIN",
            "school_name": "School B",
        },
    ).json()
    login = c.post(
        "/api/v1/auth/login", json={"email": "admin.a", "password": "Temporary-password-123"}
    ).json()
    renewed = c.post(
        "/api/v1/auth/password",
        headers={"Authorization": "Bearer " + login["access_token"]},
        json={"current_password": "Temporary-password-123", "new_password": "Fresh-secure-password-9876"},
    ).json()
    headers = {"Authorization": "Bearer " + renewed["access_token"]}
    assert [x["id"] for x in c.get("/api/v1/staff", headers=headers).json()] == [a["id"]]
    assert (
        c.post(
            "/api/v1/staff/announcements",
            headers=headers,
            json={"title": "Test", "body": "Message", "recipient_ids": [b["id"]]},
        ).status_code
        == 403
    )
    assert (
        c.put(
            "/api/v1/staff/" + p["teacher3"]["id"] + "/state",
            headers=p["teacher3"]["headers"],
            json={"active": False},
        ).status_code
        == 403
    )
    assert (
        c.put(
            "/api/v1/staff/" + p["teacher3"]["id"] + "/state", headers=root, json={"active": False}
        ).status_code
        == 200
    )
    assert c.get("/api/v1/users/me", headers=p["teacher3"]["headers"]).status_code == 401
