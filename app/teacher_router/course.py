from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import Course, User, Department,Role
from ..schemas import CourseCreate, CourseOut,AssignCourse
from ..security import get_current_user

from ..logger import logger

router = APIRouter()

# Create a new course (only for teachers)
@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Teacher":
        logger.warning(f"Unauthorized course creation attempt by user {current_user['user_id']}")
        raise HTTPException(status_code=403, detail="Only teachers can create courses.")

    department = db.query(Department).filter_by(department_id=course.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")

    new_course = Course(
        course_title=course.course_title,
        course_code=course.course_code,
        credits=course.credits,
        instructor_id=current_user["user_id"],
        department_id=course.department_id
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    logger.info(f"Course created by teacher {current_user['user_id']}: {course.course_code}")
    return new_course

# Get all courses created by the logged-in teacher
@router.get("/courses", response_model=list[CourseOut])
def get_courses_by_teacher(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view their courses.")

    courses = db.query(Course).filter(Course.instructor_id == current_user["user_id"]).all()
    return courses

# Update a course (only if owned by the teacher)
@router.put("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    updated_course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Teacher":
        logger.warning(f"Unauthorized course update attempt by user {current_user['user_id']}")
        raise HTTPException(status_code=403, detail="Only teachers can update courses.")

    course = db.query(Course).filter(
        Course.course_id == course_id,
        Course.instructor_id == current_user["user_id"]
    ).first()

    if not course:
        logger.warning(f"Course not found or unauthorized update attempt by user {current_user['user_id']}")
        raise HTTPException(status_code=404, detail="Course not found or not authorized.")

    # Check if new department exists
    department = db.query(Department).filter_by(department_id=updated_course.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")

    course.course_title = updated_course.course_title
    course.course_code = updated_course.course_code
    course.credits = updated_course.credits
    course.department_id = updated_course.department_id

    db.commit()
    db.refresh(course)

    logger.info(f"Course updated by teacher {current_user['user_id']}: {course.course_code}")
    return course

# Delete a course (only if owned by the teacher)
@router.delete("/courses/{course_id}", status_code=200)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"User info: {current_user}")

    if current_user["role"] != "Teacher":
        logger.warning(f"Unauthorized course delete attempt by user {current_user['user_id']}")
        raise HTTPException(status_code=403, detail="Only teachers can delete courses.")

    course = db.query(Course).filter(
        Course.course_id == course_id,
        Course.instructor_id == current_user["user_id"]
    ).first()

    if not course:
        logger.warning(f"Course not found or not authorized for user {current_user['user_id']}")
        raise HTTPException(status_code=404, detail="Course not found or not authorized.")

    db.delete(course)
    db.commit()

    logger.info(f"Course deleted by teacher {current_user['user_id']}: {course.course_code}")
    return {"message": "Course deleted successfully"}

@router.post("/assign-course")
def assign_course_to_student(
    payload: AssignCourse,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Teacher":
        logger.warning(f"Unauthorized course assignment attempt by user {current_user['user_id']}")
        raise HTTPException(status_code=403, detail="Only teachers can assign courses.")

    course = db.query(Course).filter(Course.course_id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    student = db.query(User).join(Role).filter(User.user_id == payload.student_id, Role.role_name == "Student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if student in course.students:
        raise HTTPException(status_code=400, detail="Student is already assigned to this course.")

    course.students.append(student)
    db.commit()

    logger.info(f"Course {course.course_code} assigned to student {student.email} by teacher {current_user['user_id']}")
    return {"message": f"Course '{course.course_title}' assigned to student '{student.full_name}'."}
