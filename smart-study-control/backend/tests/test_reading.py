import io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from sqlalchemy import select
from app.models.entities import ReadingAttempt, RewardTransaction, now
from app.services.reading import parse_pdf

FACTS = [
    "Water freezes at zero degrees Celsius.",
    "Plants use sunlight to make food.",
    "Earth travels around the Sun once each year.",
]


def make_pdf(lines=FACTS):
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    kids = []
    for line in lines:
        page_id = len(objects) + 1
        stream_id = page_id + 1
        font_id = page_id + 2
        kids.append(page_id)
        content = (
            "BT /F1 18 Tf 40 180 Td (" + line.replace("(", "\\(").replace(")", "\\)") + ") Tj ET"
        ).encode("ascii")
        objects.extend(
            [
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 640 240] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {stream_id} 0 R >>".encode(),
                b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            ]
        )
    objects[1] = (
        f"<< /Type /Pages /Kids [{' '.join(str(k) + ' 0 R' for k in kids)}] /Count {len(kids)} >>".encode()
    )
    value = b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(value))
        value += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(value)
    value += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    value += b"".join(f"{off:010d} 00000 n \n".encode() for off in offsets[1:])
    value += f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return value


def lesson_content():
    return {
        "title": "Tabiat haqida",
        "summary": "Kitobdagi uch faktni tushuntiruvchi dars.",
        "concepts": [
            {
                "id": "water",
                "title": "Suv",
                "explanation": "Suvning muzlash harorati.",
                "source_page": 1,
                "source_quote": FACTS[0],
            }
        ],
        "connections": [],
        "questions": [
            {
                "prompt": "Water freezes at?",
                "options": ["Zero degrees Celsius", "One hundred degrees Celsius"],
                "correct_index": 0,
                "explanation": "The book states zero degrees Celsius.",
                "source_page": 1,
                "source_quote": FACTS[0],
            },
            {
                "prompt": "Plants use what to make food?",
                "options": ["Sunlight", "Moonlight"],
                "correct_index": 0,
                "explanation": "Sunlight supports food production.",
                "source_page": 2,
                "source_quote": FACTS[1],
            },
            {
                "prompt": "Earth travels around?",
                "options": ["The Sun", "Mars"],
                "correct_index": 0,
                "explanation": "Earth orbits the Sun.",
                "source_page": 3,
                "source_quote": FACTS[2],
            },
        ],
    }


@pytest.fixture
def reading(people, tmp_path, monkeypatch):
    from app.core import config
    from app.api import reading as routes
    from dataclasses import replace

    monkeypatch.setattr(routes, "settings", replace(config.settings, upload_dir=str(tmp_path / "uploads")))
    c, factory, p = people
    ph = p["parent1"]["headers"]
    sh = p["student0"]["headers"]
    b = c.post(
        "/api/v1/books",
        headers=ph,
        data={"title": "Nature facts"},
        files={"file": ("book.pdf", make_pdf(), "application/pdf")},
    )
    assert b.status_code == 201, b.text
    book = b.json()
    l = c.post(
        f"/api/v1/books/{book['id']}/lessons",
        headers=ph,
        json={"start_page": 1, "end_page": 3, "content": lesson_content()},
    )
    assert l.status_code == 201, l.text
    lesson = l.json()
    publish = c.post(
        f"/api/v1/reading/lessons/{lesson['id']}/publish",
        headers=ph,
        json={"expected_version": 1, "answer_key_validated": True},
    )
    assert publish.status_code == 200, publish.text
    c.put(
        f"/api/v1/automation/children/{p['student0']['id']}",
        headers=ph,
        json={"enabled": True, "auto_practice": False, "daily_reward_limit": 60, "max_tasks_per_day": 2},
    )
    plan = c.post(
        f"/api/v1/books/{book['id']}/plans",
        headers=ph,
        json={
            "student_id": p["student0"]["id"],
            "start_page": 1,
            "end_page": 3,
            "reward_minutes": 15,
            "auto_reward": True,
        },
    )
    assert plan.status_code == 201, plan.text
    return c, factory, p, book, lesson, plan.json()


def start(c, p, plan, lesson, key="reading-attempt-test-0001"):
    for page_number in range(lesson["start_page"], lesson["end_page"] + 1):
        marked = c.post(
            f"/api/v1/reading/plans/{plan['id']}/progress",
            headers=p["student0"]["headers"],
            json={"page_number": page_number, "reported_seconds": 0},
        )
        assert marked.status_code == 200, marked.text
    result = c.post(
        f"/api/v1/reading/plans/{plan['id']}/lessons/{lesson['id']}/attempts",
        headers={**p["student0"]["headers"], "Idempotency-Key": key},
        json={},
    )
    assert result.status_code == 200, result.text
    return result.json()


def test_super_admin_can_upload_and_own_a_book(reading):
    c, _, p, _, _, _ = reading
    response = c.post(
        "/api/v1/books",
        headers=p["super_admin5"]["headers"],
        data={"title": "Admin curriculum"},
        files={"file": ("book.pdf", make_pdf(), "application/pdf")},
    )
    assert response.status_code == 201, response.text
    book = response.json()
    assert book["title"] == "Admin curriculum"
    assert book["owner_id"] == p["super_admin5"]["id"]


def test_test_requires_student_to_mark_every_lesson_page_first(reading):
    c, _, p, _, lesson, plan = reading
    path = f"/api/v1/reading/plans/{plan['id']}/lessons/{lesson['id']}/attempts"
    headers = {**p["student0"]["headers"], "Idempotency-Key": "reading-pages-required-0001"}
    rejected = c.post(path, headers=headers, json={})
    assert rejected.status_code == 409
    assert "every page" in rejected.json()["error"]["message"]
    for page_number in (1, 2):
        assert c.post(
            f"/api/v1/reading/plans/{plan['id']}/progress",
            headers=p["student0"]["headers"],
            json={"page_number": page_number, "reported_seconds": 120},
        ).status_code == 200
    assert c.post(path, headers=headers, json={}).status_code == 409
    assert c.post(
        f"/api/v1/reading/plans/{plan['id']}/progress",
        headers=p["student0"]["headers"],
        json={"page_number": 3, "reported_seconds": 120},
    ).status_code == 200
    assert c.post(path, headers=headers, json={}).status_code == 200


def correct_answers(attempt):
    valid = {"Zero degrees Celsius", "Sunlight", "The Sun"}
    return {q["id"]: next(i for i, v in enumerate(q["options"]) if v in valid) for q in attempt["questions"]}


def test_pdf_extraction_is_real_and_rejects_invalid_document(tmp_path):
    path = tmp_path / "book.pdf"
    path.write_bytes(make_pdf())
    result = parse_pdf(path)
    assert result["page_count"] == 3
    assert FACTS[1] in result["pages"][1]["text"]
    path.write_bytes(b"%PDF-not-valid")
    with pytest.raises(Exception) as exc:
        parse_pdf(path)
    assert exc.value.status_code == 422


def test_local_ocr_extracts_actual_rasterized_page(tmp_path):
    import shutil

    if not shutil.which("tesseract") or not Path("/usr/bin/pdftoppm").exists():
        pytest.skip("OCR tools not installed")
    path = tmp_path / "book.pdf"
    path.write_bytes(make_pdf())
    result = parse_pdf(path, "ocr", 1, 1)
    assert result["pages"][0]["method"] == "OCR_UNVERIFIED"
    assert "Water freezes" in result["pages"][0]["text"]


def test_reading_self_report_never_grants_reward(reading):
    c, _, p, b, l, plan = reading
    for page in range(1, 4):
        r = c.post(
            f"/api/v1/reading/plans/{plan['id']}/progress",
            headers=p["student0"]["headers"],
            json={"page_number": page, "reported_seconds": 3600},
        )
        assert r.status_code == 200, r.text
    assert r.json()["self_reported_percent"] == 100 and r.json()["checked_percent"] == 0
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 0


def test_validated_test_grants_once_and_preserves_answer_secrecy(reading):
    c, factory, p, b, l, plan = reading
    sh = p["student0"]["headers"]
    material = c.get(f"/api/v1/reading/lessons/{l['id']}", headers=sh).json()
    assert "questions" not in material["content"]
    a = start(c, p, plan, l)
    assert "answer_key" not in a and "review" not in a
    assert all("correct_index" not in q for q in a["questions"])
    answers = correct_answers(a)
    for _ in range(2):
        finish = c.post(f"/api/v1/reading/attempts/{a['id']}/finish", headers=sh, json={"answers": answers})
        assert finish.status_code == 200, finish.text
        assert finish.json()["result"]["reward"] == {"state": "GRANTED", "minutes": 15}
    assert c.get("/api/v1/rewards/wallet", headers=sh).json()["available"] == 15
    progress = c.get(f"/api/v1/reading/plans/{plan['id']}", headers=sh).json()["progress"]
    assert progress["checked_percent"] == 100 and progress["self_reported_percent"] == 0
    with factory() as db:
        assert (
            len(list(db.scalars(select(RewardTransaction).where(RewardTransaction.origin.like("reading:%")))))
            == 1
        )


def test_simultaneous_finish_cannot_double_reward(reading):
    c, _, p, b, l, plan = reading
    a = start(c, p, plan, l)
    body = {"answers": correct_answers(a)}

    def finish(_):
        return c.post(
            f"/api/v1/reading/attempts/{a['id']}/finish", headers=p["student0"]["headers"], json=body
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(finish, [1, 2]))
    assert [r.status_code for r in results] == [200, 200], [r.text for r in results]
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 15


def test_private_book_isolated_and_fake_source_rejected(reading):
    c, _, p, b, l, plan = reading
    for name in ["parent2", "teacher3", "super_admin5"]:
        assert c.get(f"/api/v1/books/{b['id']}", headers=p[name]["headers"]).status_code == 403
        assert c.get(f"/api/v1/reading/plans/{plan['id']}", headers=p[name]["headers"]).status_code == 403
    bad = lesson_content()
    bad["questions"][0]["source_quote"] = "This quote does not exist in the book."
    r = c.post(
        f"/api/v1/books/{b['id']}/lessons",
        headers=p["parent1"]["headers"],
        json={"start_page": 1, "end_page": 3, "content": bad},
    )
    assert r.status_code == 422
    assert (
        c.post(
            f"/api/v1/reading/lessons/{l['id']}/publish",
            headers=p["student0"]["headers"],
            json={"expected_version": 1, "answer_key_validated": True},
        ).status_code
        == 403
    )


def test_changed_source_version_and_expired_test_cannot_reward(reading):
    c, factory, p, b, l, plan = reading
    a = start(c, p, plan, l)
    with factory.begin() as db:
        db.get(ReadingAttempt, a["id"]).expires_at = now() - timedelta(seconds=1)
    r = c.post(
        f"/api/v1/reading/attempts/{a['id']}/finish",
        headers=p["student0"]["headers"],
        json={"answers": correct_answers(a)},
    )
    assert r.status_code == 409
    a = start(c, p, plan, l, "reading-attempt-test-0002")
    assert (
        c.put(
            f"/api/v1/reading/lessons/{l['id']}",
            headers=p["parent1"]["headers"],
            json={"start_page": 1, "end_page": 3, "content": lesson_content()},
        ).status_code
        == 200
    )
    assert (
        c.post(
            f"/api/v1/reading/attempts/{a['id']}/finish",
            headers=p["student0"]["headers"],
            json={"answers": correct_answers(a)},
        ).status_code
        == 409
    )


def test_duplicate_assignment_cannot_award_same_lesson_again(reading):
    c, _, p, b, l, plan = reading
    first = start(c, p, plan, l)
    result = c.post(
        f"/api/v1/reading/attempts/{first['id']}/finish",
        headers=p["student0"]["headers"],
        json={"answers": correct_answers(first)},
    )
    assert result.json()["result"]["reward"]["state"] == "GRANTED"
    second_plan = c.post(
        f"/api/v1/books/{b['id']}/plans",
        headers=p["parent1"]["headers"],
        json={
            "student_id": p["student0"]["id"],
            "start_page": 1,
            "end_page": 3,
            "reward_minutes": 15,
            "auto_reward": True,
        },
    ).json()
    second = start(c, p, second_plan, l, "different-plan-attempt")
    result = c.post(
        f"/api/v1/reading/attempts/{second['id']}/finish",
        headers=p["student0"]["headers"],
        json={"answers": correct_answers(second)},
    )
    assert result.json()["result"]["reward"] == {"state": "ALREADY_GRANTED", "minutes": 0}
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 15


def test_reading_budget_and_human_review_are_enforced(reading):
    c, _, p, b, l, plan = reading
    ph = p["parent1"]["headers"]
    sh = p["student0"]["headers"]
    c.put(
        f"/api/v1/automation/children/{p['student0']['id']}",
        headers=ph,
        json={"enabled": False, "auto_practice": False, "daily_reward_limit": 10, "max_tasks_per_day": 2},
    )
    a = start(c, p, plan, l)
    finished = c.post(
        f"/api/v1/reading/attempts/{a['id']}/finish", headers=sh, json={"answers": correct_answers(a)}
    ).json()
    assert finished["result"]["reward"]["state"] == "HUMAN_REQUIRED"
    grant = c.post(f"/api/v1/reading/attempts/{a['id']}/approve-reward", headers=ph, json={}).json()
    assert grant["result"]["reward"]["state"] == "BUDGET_REACHED"
    assert (
        c.post(f"/api/v1/reading/attempts/{a['id']}/approve-reward", headers=sh, json={}).status_code == 403
    )


def test_revoked_guardian_cannot_read_child_history(reading):
    from app.models.entities import ParentLink

    c, factory, p, b, l, plan = reading
    with factory.begin() as db:
        db.scalar(select(ParentLink).where(ParentLink.parent_id == p["parent1"]["id"])).consent = False
    headers = p["parent1"]["headers"]
    assert c.get(f"/api/v1/reading/plans/{plan['id']}", headers=headers).status_code == 403
    assert c.get(f"/api/v1/reading/plans/{plan['id']}/attempts", headers=headers).status_code == 403
    assert c.get("/api/v1/reading/plans", headers=headers).json() == []


def test_teacher_loses_reading_results_after_student_leaves_class(reading):
    from app.models.entities import Classroom, ClassroomMember, ReadingPlan

    c, factory, p, b, l, _ = reading
    with factory.begin() as db:
        classroom = Classroom(name="Science", teacher_id=p["teacher3"]["id"])
        db.add(classroom)
        db.flush()
        member = ClassroomMember(classroom_id=classroom.id, student_id=p["student0"]["id"])
        db.add(member)
        plan = ReadingPlan(
            book_id=b["id"],
            student_id=p["student0"]["id"],
            assigned_by=p["teacher3"]["id"],
            classroom_id=classroom.id,
            start_page=1,
            end_page=3,
            reward_minutes=0,
        )
        db.add(plan)
        db.flush()
        plan_id, member_id = plan.id, member.id
    headers = p["teacher3"]["headers"]
    assert c.get(f"/api/v1/reading/plans/{plan_id}", headers=headers).status_code == 200
    with factory.begin() as db:
        db.delete(db.get(ClassroomMember, member_id))
    assert c.get(f"/api/v1/reading/plans/{plan_id}", headers=headers).status_code == 403
    assert c.get("/api/v1/reading/plans", headers=headers).json() == []


def test_edit_publish_race_never_publishes_unreviewed_version(reading):
    c, _, p, b, l, _ = reading
    path = f"/api/v1/reading/lessons/{l['id']}"
    headers = p["parent1"]["headers"]

    def edit():
        return c.put(
            path, headers=headers, json={"start_page": 1, "end_page": 3, "content": lesson_content()}
        )

    def publish():
        return c.post(
            path + "/publish", headers=headers, json={"expected_version": 1, "answer_key_validated": True}
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        edit_future = executor.submit(edit)
        publish_future = executor.submit(publish)
        changed, published = edit_future.result(), publish_future.result()
    assert changed.status_code == 200, changed.text
    assert published.status_code in (200, 409), published.text
    state = c.get(path, headers=headers).json()
    assert state["version"] == 2 and state["status"] == "DRAFT"
