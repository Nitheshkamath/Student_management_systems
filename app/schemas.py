from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date,datetime

class UserCreate(BaseModel):
    full_name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    date_of_birth: Optional[date] = None

class Login(BaseModel):
    email: EmailStr
    password: str

class DepartmentCreate(BaseModel):
    department_name: str
    head_user_id: int

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    head_user_id: Optional[int] = None

class CourseCreate(BaseModel):
    course_title: str
    course_code: str
    credits: int
    department_id: int


class CourseOut(BaseModel):
    course_id: int
    course_title: str
    course_code: str
    created_at:datetime
    credits: int

class AssignCourse(BaseModel):
    course_id: int
    student_id: int

class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    date_of_birth: date
