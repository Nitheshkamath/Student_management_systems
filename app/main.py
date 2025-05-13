from fastapi import FastAPI
from .database import Base, engine
from .admin_router import auth, department
from .teacher_router import teacher_auth,course,student_crud
from .student_router import student_auth,student_course
from .excel_router import report_export,certificate

from . import model

app = FastAPI(title="Student Management System")

@app.on_event("startup")
def on_startup():
    print(" tables created")
    Base.metadata.create_all(bind=engine)



app.include_router(auth.router, prefix="/admin", tags=["Admin Auth"])
app.include_router(department.router, prefix="/admin", tags=["Department Management"])
app.include_router(teacher_auth.router,prefix="/teacher",tags=["Teacher auth"])
app.include_router(course.router,prefix="/teacher",tags=["Courses"])
app.include_router(student_crud.router,prefix="/teacher",tags=["Students CRUD"])
app.include_router(student_auth.router,prefix="/student",tags=["Student auth"])
app.include_router(student_course.router,prefix="/student",tags=["view Course"])
app.include_router(report_export.router, prefix="/reports", tags=["Report Export"])
app.include_router(certificate.router, prefix="/reports", tags=["Course Completion"])


@app.get("/")
def home():
    return {"Welcome to Student Management"}
