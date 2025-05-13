import os
from ..logger import logger
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from ..database import get_db
from ..security import get_current_user
from ..model import User, Course

# Configure router
router = APIRouter()

@router.get("/certificates/student/{student_id}")
def generate_certificate(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"User '{current_user['username']}' with role '{current_user['role']}' requested certificate for student_id={student_id}, course_id={course_id}")

    if current_user["role"] != "Teacher":
        logger.warning(f"Unauthorized certificate access attempt by '{current_user['username']}'")
        raise HTTPException(status_code=403, detail="Only teachers can issue certificates")

    teacher = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    student = db.query(User).filter(User.user_id == student_id).first()
    course = db.query(Course).filter(Course.course_id == course_id).first()

    if not student or not course:
        logger.error("Student or course not found in the database")
        raise HTTPException(status_code=404, detail="Student or course not found")

    if course.instructor_id != teacher.user_id:
        logger.warning(f"Teacher '{teacher.full_name}' is not the instructor for course '{course.course_title}'")
        raise HTTPException(status_code=403, detail="You are not the instructor for this course")

    if student not in course.students:
        logger.warning(f"Student '{student.full_name}' is not enrolled in course '{course.course_title}'")
        raise HTTPException(status_code=400, detail="Student not enrolled in this course")

    try:
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("certificate_templates.html")
        html_content = template.render(
            student_name=student.full_name,
            course_title=course.course_title,
            instructor_name=teacher.full_name,
            date=datetime.now().strftime("%B %d, %Y")
        )
        logger.info(f"Certificate generated successfully for student '{student.full_name}'")
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        raise HTTPException(status_code=500, detail="Error rendering certificate")

    os.makedirs("certificates", exist_ok=True)
    output_path = f"certificates/certificate_{student_id}_{course_id}.pdf"

    try:
        with open(output_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            logger.error("PDF generation failed due to rendering error")
            raise HTTPException(status_code=500, detail="Error generating PDF")
        logger.info(f"PDF certificate successfully generated at '{output_path}'")
    except Exception as e:
        logger.error(f"PDF generation exception: {e}")
        raise HTTPException(status_code=500, detail="Error generating PDF")

    return FileResponse(output_path, filename="course_certificate.pdf", media_type="application/pdf")
