from fastapi import APIRouter, HTTPException, Depends
from openpyxl import Workbook
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import User
from ..security import get_current_user
from ..logger import logger

# Initialize router
router = APIRouter()

@router.get("/export/students/excel")
def export_students_excel(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    logger.info(f"User '{current_user['username']}' with role '{current_user['role']}' requested student Excel export")

    if current_user["role"] != "Admin":
        logger.warning(f"Unauthorized export attempt by user '{current_user['username']}'")
        raise HTTPException(status_code=403, detail="Admins only")

    students = db.query(User).filter(User.role.has(role_name="Student")).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(["Student ID", "Student Name", "Email", "Course", "Department", "Instructor"])

    for student in students:
        for course in student.courses:
            dept = course.department.department_name if course.department else "N/A"
            instructor = course.instructor.full_name if course.instructor else "N/A"
            ws.append([student.user_id, student.full_name, student.email, course.course_title, dept, instructor])

    file_path = "student_report.xlsx"
    try:
        wb.save(file_path)
        logger.info(f"Excel file saved successfully {file_path}'")
    except Exception as e:
        logger.error(f"Failed to save Excel file: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Excel report")

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_path
    )
