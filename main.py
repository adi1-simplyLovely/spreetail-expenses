from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uvicorn

from database import engine, Base
from auth import get_current_user_optional
from routers import auth_routes, group_routes, expense_routes, balance_routes, settlement_routes

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(title="SplitEase", description="Shared Expenses App")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth_routes.router, tags=["Authentication"])
app.include_router(group_routes.router)
app.include_router(expense_routes.router)
app.include_router(balance_routes.router)
app.include_router(settlement_routes.router)
# Other routers will be included here as we build them
# app.include_router(import_routes.router)


@app.get("/")
async def root(user=Depends(get_current_user_optional)):
    """
    Root endpoint. 
    Redirects to /dashboard if logged in, otherwise redirects to /login.
    """
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


# Temporary dashboard route just to test the login redirect
@app.get("/dashboard")
async def dashboard(request: Request, user=Depends(get_current_user_optional)):
    """Temporary dashboard just to confirm login works."""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


if __name__ == "__main__":
    # Run the app on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
