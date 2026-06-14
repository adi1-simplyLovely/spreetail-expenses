import json
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User, Group, GroupMember, Expense, ExpenseSplit
from auth import get_current_user
from utils.split_calculator import (
    calculate_equal_split, 
    calculate_percentage_split,
    calculate_unequal_split,
    calculate_share_split
)
from utils.currency import convert_to_inr

router = APIRouter(tags=["Expenses"])
templates = Jinja2Templates(directory="templates")

@router.get("/groups/{group_id}/expenses", response_class=HTMLResponse)
async def list_expenses(
    request: Request, 
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all expenses in a specific group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # We will fetch all non-settlement expenses for this group
    expenses = db.query(Expense).filter(
        Expense.group_id == group_id,
        Expense.is_settlement == False
    ).order_by(Expense.date.desc()).all()
    
    return templates.TemplateResponse(request=request, name="expense_list.html", context= 
        {"request": request, "user": current_user, "group": group, "expenses": expenses}
    )


@router.get("/groups/{group_id}/expenses/add", response_class=HTMLResponse)
async def add_expense_page(
    request: Request, 
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Render the add expense form with dynamic split types."""
    group = db.query(Group).filter(Group.id == group_id).first()
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.left_at == None
    ).all()
    
    return templates.TemplateResponse(request=request, name="expense_add.html", context= 
        {"request": request, "user": current_user, "group": group, "members": members}
    )


@router.post("/groups/{group_id}/expenses")
async def create_expense(
    request: Request,
    group_id: int,
    description: str = Form(...),
    date_val: date = Form(alias="date"),
    paid_by: int = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    split_type: str = Form(...),
    split_with: List[int] = Form(...),
    split_details: Optional[str] = Form(None), # JSON string mapping user_id to value (pct, exact, or share)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new expense and its splits in one transaction."""
    amount_inr = convert_to_inr(amount, currency)
    
    # Create the Expense record
    new_expense = Expense(
        group_id=group_id,
        description=description,
        paid_by=paid_by,
        amount=amount,
        currency=currency.upper(),
        amount_inr=amount_inr,
        split_type=split_type,
        date=date_val,
        is_settlement=False
    )
    db.add(new_expense)
    db.flush() # Flush to get new_expense.id before committing
    
    # Parse split_details if provided
    details_dict = {}
    if split_details:
        try:
            # Expected format: {"1": 30, "2": 70}
            raw_details = json.loads(split_details)
            details_dict = {int(k): float(v) for k, v in raw_details.items()}
        except json.JSONDecodeError:
            pass

    # Calculate splits
    splits = {}
    if split_type == "equal":
        splits = calculate_equal_split(amount_inr, split_with)
    elif split_type == "percentage":
        splits = calculate_percentage_split(amount_inr, details_dict)
    elif split_type == "unequal":
        splits = calculate_unequal_split(details_dict)
    elif split_type == "share":
        splits = calculate_share_split(amount_inr, details_dict)
        
    # Store Expense Splits
    for user_id, amount_owed in splits.items():
        split_record = ExpenseSplit(
            expense_id=new_expense.id,
            user_id=user_id,
            amount_owed=amount_owed
        )
        db.add(split_record)
        
    # Commit the transaction
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group_id}/expenses", status_code=status.HTTP_302_FOUND)


@router.get("/expenses/{expense_id}", response_class=HTMLResponse)
async def expense_detail(
    request: Request,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Show detailed view of a specific expense and who owes what."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    return templates.TemplateResponse(request=request, name="expense_detail.html", context= 
        {"request": request, "user": current_user, "expense": expense}
    )


@router.post("/expenses/{expense_id}/delete")
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hard delete an expense. The prompt schema does not have a deleted_at column."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    group_id = expense.group_id
    db.delete(expense) # Cascade deletes splits automatically
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group_id}/expenses", status_code=status.HTTP_302_FOUND)
