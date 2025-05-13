from fastapi import APIRouter, Depends, HTTPException, Path,status
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import User, Role
from ..schemas import UserCreate,Login
from ..security import hash_password,verify_password,create_access_token,get_current_user
from ..logger import logger



router = APIRouter()

@router.post("/register-teacher")
def register_teacher(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        logger.warning(f"Unauthorized attempt by {current_user['user_id']} to register teacher.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can register teachers.")

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    role = db.query(Role).filter_by(role_name="Teacher").first()
    if not role:
        role = Role(role_name="Teacher")
        db.add(role)
        db.commit()
        db.refresh(role)
        logger.info("Teacher role created.")

    new_teacher = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        date_of_birth=user.date_of_birth,
        role_id=role.role_id
    )
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    logger.info(f"Teacher registered successfully: {new_teacher.email}")
    return {"message": "Teacher registered successfully"}


@router.post("/login-teacher")
def login_teacher(login_data: Login, db: Session = Depends(get_db)):
    user = db.query(User).join(Role).filter(
        User.email == login_data.email,
        Role.role_name == "Teacher"
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(
        data={"user_id": user.user_id, "role": "Teacher"}
    )

    logger.info(f"Teacher login successful: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.put("/update-teacher/{teacher_id}")
def update_teacher(
    teacher_id: int,
    updated_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can update teachers.")

    teacher = db.query(User).join(Role).filter(User.user_id == teacher_id, Role.role_name == "Teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found.")

    teacher.full_name = updated_data.full_name
    teacher.email = updated_data.email
    teacher.password_hash = hash_password(updated_data.password)
    teacher.date_of_birth = updated_data.date_of_birth

    db.commit()
    db.refresh(teacher)

    logger.info(f"Teacher updated: {teacher.email}")
    return {"message": "Teacher updated successfully"}


@router.delete("/delete-teacher/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can delete teachers.")

    teacher = db.query(User).join(Role).filter(User.user_id == teacher_id, Role.role_name == "Teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found.")

    db.delete(teacher)
    db.commit()

    logger.info(f"Teacher deleted: {teacher.email}")
    return {"message": "Teacher deleted successfully"}