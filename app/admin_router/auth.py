from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from ..database import get_db
from ..model import User, Role
from ..schemas import UserCreate, Login
from ..security import hash_password, verify_password, create_access_token
from ..logger import logger

router = APIRouter()



@router.post("/register-admin")
def register_admin(user: UserCreate, secret_key: str, db: Session = Depends(get_db)):
    expected_secret = os.getenv("SUPER_ADMIN_SECRET")

    if secret_key != expected_secret:
        logger.warning(f"Unauthorized admin registration attempt with key: {secret_key}")
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid secret key")

    existing_admin = db.query(User).join(Role).filter(Role.role_name == "Admin").first()
    if existing_admin:
        logger.info(f"Admin registration blocked: Admin already exists (email: {existing_admin.email})")
        raise HTTPException(status_code=400, detail="Admin already exists")

    role = db.query(Role).filter_by(role_name="Admin").first()
    if not role:
        role = Role(role_name="Admin")
        db.add(role)
        db.commit()
        db.refresh(role)
        logger.info("Admin role created.")

    new_admin = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        date_of_birth=user.date_of_birth,
        role_id=role.role_id
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    logger.info(f"Admin registered successfully: {new_admin.email}")
    return {
        "message": "Admin registered successfully",

    }


@router.post("/login-admin")

def login_admin(
    login_data:Login,
    db: Session = Depends(get_db)
):
    user = db.query(User).join(Role).filter(User.email == login_data.email, Role.role_name == "Admin").first()

    if not user:
        raise HTTPException(status_code=404, detail="Admin not found")


    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(
        data={"user_id": user.user_id, "role": "Admin"}
    )

    logger.info(f"Admin login successful: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }