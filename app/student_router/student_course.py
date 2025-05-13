from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import User
from ..schemas import CourseOut
from ..security import get_current_user
from ..logger import logger

router=APIRouter()

@router.get("/my-courses", response_model=list[CourseOut])
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Student":
        logger.warning(f"Unauthorized course view attempt by user {current_user['user_id']}")
        raise HTTPException(status_code=403, detail="Only students can view their courses.")

    student = db.query(User).filter(User.user_id == current_user["user_id"]).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student.courses