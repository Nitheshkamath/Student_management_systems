from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, func,Date
from sqlalchemy.orm import relationship
from .database import Base

# Many-to-many table between students and courses
student_courses = Table(
    "student_courses",
    Base.metadata,
    Column("student_id", ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True)
)

# Role table (Student, Teacher, Admin, etc.)
class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)

    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="SET NULL"))

    role = relationship("Role", back_populates="users")

    courses = relationship("Course", secondary=student_courses, back_populates="students")
    instructed_courses = relationship("Course", back_populates="instructor", foreign_keys='Course.instructor_id')


# Department table with a one-to-one relationship to head (User)
# Department table
class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), unique=True, nullable=False)
    head_user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), unique=True, nullable=True)

    head = relationship("User", uselist=False, foreign_keys=[head_user_id])
    courses = relationship("Course", back_populates="department", cascade="all, delete-orphan")


# Course table

class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, index=True)
    course_title = Column(String(100), nullable=False)
    course_code = Column(String(20), unique=True, nullable=False)
    credits = Column(Integer, nullable=False)

    instructor_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    instructor = relationship("User", back_populates="instructed_courses", foreign_keys=[instructor_id])

    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=True)
    department = relationship("Department", back_populates="courses", passive_deletes=True)

    created_at = Column(DateTime, default=func.now())

    students = relationship("User", secondary=student_courses, back_populates="courses")
