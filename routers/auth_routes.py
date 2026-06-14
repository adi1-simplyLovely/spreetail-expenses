import re
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import User
from auth import get_password_hash, verify_password, create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def is_valid_email(email: str) -> bool:
    """Basic regex for email validation."""
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(regex, email) is not None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login form."""
    return templates.TemplateResponse(request=request, name="login.html", context= {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login and set JWT cookie."""
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context= 
            {"request": request, "error": "Invalid email or password"}
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Redirect to dashboard and set HttpOnly cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 24 * 7, # 7 days
        samesite="lax",
    )
    return response


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render the signup form."""
    return templates.TemplateResponse(request=request, name="signup.html", context= {"request": request})


@router.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process signup and create a new user."""
    # Validations
    if not is_valid_email(email):
        return templates.TemplateResponse(request=request, name="signup.html", context= 
            {"request": request, "error": "Invalid email address format"}
        )
        
    if len(password) < 6:
        return templates.TemplateResponse(request=request, name="signup.html", context= 
            {"request": request, "error": "Password must be at least 6 characters long"}
        )
        
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(request=request, name="signup.html", context= 
            {"request": request, "error": "Email is already registered"}
        )
        
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(name=name, email=email, password_hash=hashed_password)
    
    try:
        db.add(new_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(request=request, name="signup.html", context= 
            {"request": request, "error": "Database error occurred"}
        )
        
    # Redirect to login with success message
    return templates.TemplateResponse(request=request, name="login.html", context= 
        {"request": request, "success": "Account created successfully! Please login."}
    )


@router.get("/logout")
async def logout():
    """Clear JWT cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
