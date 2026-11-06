from datetime import timedelta
from app.models.entities import LocationShare, ParentLink, now


def enable(c, p):
    result = c.put(
        "/api/v1/location/children/" + p["student0"]["id"] + "/consent",
        headers=p["parent1"]["headers"],
        json={"enabled": True, "guardian_consent": True, "max_minutes": 60},
    )
    assert result.status_code == 200, result.text


def test_location_requires_both_consents_and_never_exposes_to_staff(people):
    c, f, p = people
    s = p["student0"]["headers"]
    parent = p["parent1"]["headers"]
    child = p["student0"]["id"]
    assert (
        c.post(
            "/api/v1/location/shares", headers=s, json={"minutes": 30, "sharing_consent": True}
        ).status_code
        == 403
    )
    enable(c, p)
    assert not c.get(f"/api/v1/location/children/{child}/latest", headers=parent).json()["active"]
    started = c.post("/api/v1/location/shares", headers=s, json={"minutes": 30, "sharing_consent": True})
    assert started.status_code == 201, started.text
    ident = started.json()["id"]
    body = {"latitude": 41.31, "longitude": 69.28, "accuracy_m": 24}
    assert c.post(f"/api/v1/location/shares/{ident}/point", headers=s, json=body).status_code == 200
    latest = c.get(f"/api/v1/location/children/{child}/latest", headers=parent).json()
    assert latest["latitude"] == 41.31 and not latest["stale"]
    for person in ["teacher3", "super_admin5", "parent2"]:
        assert (
            c.get(f"/api/v1/location/children/{child}/latest", headers=p[person]["headers"]).status_code
            == 403
        )
    assert c.post(f"/api/v1/location/shares/{ident}/stop", headers=s).status_code == 200
    with f() as db:
        assert db.get(LocationShare, ident).latitude is None


def test_location_expiry_revocation_and_multiple_guardians(people):
    c, f, p = people
    enable(c, p)
    child = p["student0"]["id"]
    s = p["student0"]["headers"]
    with f.begin() as db:
        db.add(ParentLink(parent_id=p["parent2"]["id"], child_id=child, consent=True))
    ident = c.post(
        "/api/v1/location/shares", headers=s, json={"minutes": 30, "sharing_consent": True}
    ).json()["id"]
    c.post(
        f"/api/v1/location/shares/{ident}/point",
        headers=s,
        json={"latitude": 0, "longitude": 0, "accuracy_m": 100},
    )
    assert c.get(f"/api/v1/location/children/{child}/latest", headers=p["parent2"]["headers"]).json()[
        "active"
    ]
    with f.begin() as db:
        db.get(LocationShare, ident).expires_at = now() - timedelta(seconds=1)
    assert (
        c.post(
            f"/api/v1/location/shares/{ident}/point",
            headers=s,
            json={"latitude": 1, "longitude": 1, "accuracy_m": 0},
        ).status_code
        == 409
    )
    with f() as db:
        assert db.get(LocationShare, ident).latitude is None
    ident = c.post(
        "/api/v1/location/shares", headers=s, json={"minutes": 30, "sharing_consent": True}
    ).json()["id"]
    c.put(
        f"/api/v1/location/children/{child}/consent",
        headers=p["parent2"]["headers"],
        json={"enabled": False, "guardian_consent": True, "max_minutes": 60},
    )
    assert not c.get(f"/api/v1/location/children/{child}/latest", headers=s).json()["active"]
    with f() as db:
        assert db.get(LocationShare, ident).status == "REVOKED"
