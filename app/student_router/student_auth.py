from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import User, Role
from ..schemas import Login
from ..security import verify_password, create_access_token
from ..logger import logger

router = APIRouter()

@router.post("/login-student")
def login_student(
    login_data: Login,
    db: Session = Depends(get_db)
):
    user = db.query(User).join(Role).filter(
        User.email == login_data.email,
        Role.role_name == "Student"
    ).first()

    if not user:
        logger.warning(f"Student login failed: No user found with email {login_data.email}")
        raise HTTPException(status_code=404, detail="Student not found")

    if not verify_password(login_data.password, user.password_hash):
        logger.warning(f"Student login failed: Incorrect password for {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(
        data={"user_id": user.user_id, "role": "Student"}
    )

    logger.info(f"Student login successful: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
