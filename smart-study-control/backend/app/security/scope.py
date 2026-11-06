from fastapi import HTTPException
from sqlalchemy import select
from app.models.entities import ParentLink, ClassroomMember, Classroom, Assignment, Device


def guardian(db, user, child):
    return (
        user.role == "PARENT"
        and db.scalar(
            select(ParentLink.id).where(
                ParentLink.parent_id == user.id, ParentLink.child_id == child, ParentLink.consent.is_(True)
            )
        )
        is not None
    )


def academic(db, user, child):
    if user.id == child or guardian(db, user, child):
        return True
    return (
        user.role == "TEACHER"
        and db.scalar(
            select(ClassroomMember.id)
            .join(Classroom, Classroom.id == ClassroomMember.classroom_id)
            .where(Classroom.teacher_id == user.id, ClassroomMember.student_id == child)
        )
        is not None
    )


def assignment_access(db, user, ident, review=False):
    row = db.get(Assignment, ident)
    if not row:
        raise HTTPException(404, "Assignment not found")
    if row.status == "DRAFT" and row.owner_id != user.id:
        raise HTTPException(403, "Draft assignment is private")
    allowed = (
        row.owner_id == user.id
        or guardian(db, user, row.student_id)
        or (not review and row.student_id == user.id)
    )
    if not allowed:
        raise HTTPException(403, "Assignment access denied")
    return row


def device_access(db, user, ident, write=False):
    row = db.get(Device, ident)
    if not row:
        raise HTTPException(404, "Device not found")
    if not (guardian(db, user, row.student_id) or (not write and row.student_id == user.id)):
        raise HTTPException(403, "Household device access denied")
    return row
