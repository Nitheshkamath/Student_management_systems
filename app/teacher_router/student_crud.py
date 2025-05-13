from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import User, Role
from typing import List
from ..schemas import UserCreate,UserOut
from ..security import get_current_user, hash_password
from ..logger import logger

router = APIRouter()

@router.get("/all-students", response_model=List[UserOut])
def get_all_students(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ["Admin", "Teacher"]:
        raise HTTPException(status_code=403, detail="Only admins and teachers can view student records.")

    students = db.query(User).join(Role).filter(Role.role_name == "Student").all()
    return students

@router.post("/register-student")
def register_student(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Teacher":
        logger.warning(f"Unauthorized attempt by {current_user['user_id']} to register student.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can register students.")

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        logger.warning(f"Student registration failed: Email already exists - {user.email}")
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    role = db.query(Role).filter_by(role_name="Student").first()
    if not role:
        role = Role(role_name="Student")
        db.add(role)
        db.commit()
        db.refresh(role)
        logger.info("Student role created.")

    new_student = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        date_of_birth=user.date_of_birth,
        role_id=role.role_id
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    logger.info(f"Student registered successfully by teacher {current_user['user_id']}: {new_student.email}")
    return {"message": "Student registered successfully"}
# Update a student
@router.put("/update-student/{student_id}")
def update_student(
    student_id: int,
    updated_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ["Admin", "Teacher"]:
        raise HTTPException(status_code=403, detail="Only admins can update students.")

    student = db.query(User).join(Role).filter(User.user_id == student_id, Role.role_name == "Student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    student.full_name = updated_data.full_name
    student.email = updated_data.email
    student.password_hash = hash_password(updated_data.password)
    student.date_of_birth = updated_data.date_of_birth

    db.commit()
    db.refresh(student)

    logger.info(f"Student updated: {student.email}")
    return {"message": "Student updated successfully"}

# Delete a student
@router.delete("/delete-student/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ["Admin", "Teacher"]:
        raise HTTPException(status_code=403, detail="Only admins can delete students.")

    student = db.query(User).join(Role).filter(User.user_id == student_id, Role.role_name == "Student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    db.delete(student)
    db.commit()

    logger.info(f"Student deleted: {student.email}")
    return {"message": "Student deleted successfully"}
