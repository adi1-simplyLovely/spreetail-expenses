from datetime import datetime, timedelta
import secrets
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from database import get_db
from models import User

# Generate a random 32-character secret key for JWT signing
# (In a real app, this should be in .env, but for this assignment we hardcode or generate it)
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing using bcrypt directly (passlib has bugs with modern bcrypt)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the hashed version."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Generates a bcrypt hash for the given password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict) -> str:
    """Creates a JWT access token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> int:
    """Verifies the JWT token and returns the user_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    FastAPI dependency to get the current authenticated user from the HttpOnly cookie.
    If the token is missing or invalid, raises 401 Unauthorized.
    """
    token = request.cookies.get("access_token")
    if not token:
        # We redirect to login instead of throwing 401 for HTML pages
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    # Remove 'Bearer ' prefix if present (though we'll store it raw in cookie)
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    user_id = verify_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    return user

def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """
    Like get_current_user, but returns None if no valid token exists,
    rather than redirecting. Useful for the root '/' route.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
        
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    try:
        user_id = verify_token(token)
        return db.query(User).filter(User.id == user_id).first()
    except HTTPException:
        return None
