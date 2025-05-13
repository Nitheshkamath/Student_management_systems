from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import User, Department,Role,Course
from ..schemas import DepartmentCreate, DepartmentUpdate
from ..security import get_current_user
from ..logger import logger
import os

router = APIRouter()
@router.post("/departments", status_code=201)
def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can create departments.")

    # Prevent duplicate department name
    existing_department = db.query(Department).filter_by(department_name=department_data.department_name).first()
    if existing_department:
        raise HTTPException(status_code=400, detail="Department already exists.")

    #  Validate head_user_id exists
    head_user = db.query(User).filter(User.user_id == department_data.head_user_id).first()
    if not head_user:
        raise HTTPException(status_code=404, detail="Head user not found.")

    #Ensure head_user_id is not already assigned to another department
    already_head = db.query(Department).filter_by(head_user_id=department_data.head_user_id).first()
    if already_head:
        raise HTTPException(status_code=400, detail="This user is already a head of another department.")

    new_department = Department(
        department_name=department_data.department_name,
        head_user_id=department_data.head_user_id
    )
    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    logger.info(f"Department created: {new_department.department_name}")
    return {"message": "Department created successfully", "department_id": new_department.department_id}


# Get All Departments
@router.get("/departments")
def get_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != ["Admin"]:
        raise HTTPException(status_code=403, detail="Only admins can view departments.")

    departments = db.query(Department).all()
    return departments

# Update Department
@router.put("/departments/{department_id}")
def update_department(
    department_id: int,
    updated_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can update departments.")

    department = db.query(Department).filter_by(department_id=department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")

    if updated_data.department_name:
        department.department_name = updated_data.department_name

    if updated_data.head_user_id:
        head_user = db.query(User).filter_by(user_id=updated_data.head_user_id).first()
        if not head_user:
            raise HTTPException(status_code=404, detail="New head user not found.")

        existing_head = db.query(Department).filter(
            Department.head_user_id == updated_data.head_user_id,
            Department.department_id != department_id
        ).first()
        if existing_head:
            raise HTTPException(status_code=400, detail="This user is already a head of another department.")

        department.head_user_id = updated_data.head_user_id

    db.commit()
    db.refresh(department)
    logger.info(f"Department updated: {department.department_name}")
    return {"message": "Department updated successfully"}


@router.delete("/departments/{department_id}", status_code=status.HTTP_200_OK)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
    ):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can delete departments.")

    department = db.query(Department).filter_by(department_id=department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")

    db.delete(department)
    db.commit()
    logger.info(f"Department deleted: {department.department_name}")
    return {"message": "Department deleted successfully"}

@router.put("/assign-department-head/{department_id}")
def assign_department_head(
    department_id: int,
    new_head_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    ):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can assign department heads.")

    department = db.query(Department).filter(Department.department_id == department_id).first()
    new_head = db.query(User).join(Role).filter(User.user_id == new_head_id, Role.role_name == "Teacher").first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")
    if not new_head:
        raise HTTPException(status_code=404, detail="Teacher not found.")

    department.head_user_id = new_head_id
    db.commit()
    logger.info(
        f"Admin {current_user['user_id']} assigned Teacher {new_head.user_id} as head of Department {department_id}")

    return {"message": f"Teacher {new_head.full_name} assigned as department head."}

@router.put("/assign-course-instructor/{course_id}")
def assign_course_instructor(
    course_id: int,
    new_instructor_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can assign instructors.")

    course = db.query(Course).filter(Course.course_id == course_id).first()
    new_instructor = db.query(User).join(Role).filter(User.user_id == new_instructor_id, Role.role_name == "Teacher").first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    if not new_instructor:
        raise HTTPException(status_code=404, detail="Teacher not found.")

    course.instructor_id = new_instructor_id
    db.commit()
    logger.info(
        f"Admin {current_user['user_id']} assigned Teacher {new_instructor.user_id} as instructor for Course {course_id}")

    return {"message": f"Teacher {new_instructor.full_name} assigned as course instructor."}
