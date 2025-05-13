from passlib.context import CryptContext
from jose import JWTError,jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException,Depends
from .database import get_db
from .model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY,  algorithms=["HS256"])

        # Ensure required fields exist in the token payload
        if "user_id" not in payload or "role" not in payload:
            raise HTTPException(status_code=400, detail="Invalid token: Missing user_id or role.")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = verify_access_token(token)
    user = db.query(User).filter(User.user_id == payload["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.user_id,
        "username": user.full_name,
        "role": user.role.role_name
    }