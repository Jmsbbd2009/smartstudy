def test_terminate_other_sessions_revokes_access_and_refresh(people):
    c, _, users = people
    owner = users["student0"]
    second = c.post("/api/v1/auth/login", json={
        "email": "student0@example.test", "password": "Strong-password-123"
    }).json()
    second_header = {"Authorization": "Bearer " + second["access_token"]}
    listed = c.get("/api/v1/profile/sessions", headers=owner["headers"]).json()
    assert len(listed) == 2
    assert sum(row["current"] for row in listed) == 1
    other_id = next(row["id"] for row in listed if not row["current"])
    assert c.delete(f"/api/v1/profile/sessions/{other_id}", headers=users["parent1"]["headers"]).status_code == 404
    assert c.post("/api/v1/profile/sessions/terminate-others", headers=owner["headers"]).status_code == 200
    assert c.get("/api/v1/users/me", headers=second_header).status_code == 401
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 401
    assert c.get("/api/v1/users/me", headers=owner["headers"]).status_code == 200


def test_session_rotation_keeps_current_family_and_rejects_current_delete(people):
    c, _, users = people
    owner = users["student0"]
    before = c.get("/api/v1/profile/sessions", headers=owner["headers"]).json()[0]
    refreshed = c.post("/api/v1/auth/refresh", json={"refresh_token": owner["tokens"]["refresh_token"]}).json()
    header = {"Authorization": "Bearer " + refreshed["access_token"]}
    after = c.get("/api/v1/profile/sessions", headers=header).json()
    assert len(after) == 1
    assert after[0]["id"] == before["id"]
    assert after[0]["current"]
    assert c.delete(f"/api/v1/profile/sessions/{before['id']}", headers=header).status_code == 409
