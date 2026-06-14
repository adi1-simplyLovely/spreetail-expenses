from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User, Group, GroupMember, Settlement, Expense
from auth import get_current_user

router = APIRouter(tags=["Settlements"])
templates = Jinja2Templates(directory="templates")

@router.get("/groups/{group_id}/settlements/add", response_class=HTMLResponse)
async def add_settlement_page(
    request: Request, 
    group_id: int, 
    from_user_id: Optional[int] = None,
    to_user_id: Optional[int] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Render the settlement form, pre-filling query params if provided."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.left_at == None
    ).all()
    
    return templates.TemplateResponse(
        "settlement_add.html", 
        {
            "request": request, 
            "user": current_user, 
            "group": group, 
            "members": members,
            "prefill_from": from_user_id,
            "prefill_to": to_user_id,
            "prefill_amount": amount
        }
    )


@router.post("/groups/{group_id}/settlements")
async def create_settlement(
    request: Request,
    group_id: int,
    from_user_id: int = Form(...),
    to_user_id: int = Form(...),
    amount: float = Form(...),
    date_val: date = Form(alias="date"),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a settlement payment and save a dummy expense row for history."""
    if from_user_id == to_user_id:
        # In a real app we'd flash an error, for now we just redirect
        return RedirectResponse(url=f"/groups/{group_id}/balances", status_code=status.HTTP_302_FOUND)
        
    # 1. Create Settlement Record
    new_settlement = Settlement(
        group_id=group_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        amount=amount,
        date=date_val,
        note=note
    )
    db.add(new_settlement)
    
    # 2. Create Dummy Expense Record (is_settlement=True)
    # This allows it to show up in the expense list history like Splitwise does,
    # but the balance engine ignores it because of is_settlement=True.
    from_user = db.query(User).filter(User.id == from_user_id).first()
    to_user = db.query(User).filter(User.id == to_user_id).first()
    
    desc = f"Payment: {from_user.name} paid {to_user.name}"
    if note:
        desc += f" ({note})"
        
    dummy_expense = Expense(
        group_id=group_id,
        description=desc,
        paid_by=from_user_id,  # Person who paid the money
        amount=amount,
        currency="INR",  # Settlements are usually in base currency
        amount_inr=amount,
        split_type="settlement",
        date=date_val,
        is_settlement=True
    )
    db.add(dummy_expense)
    
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group_id}/balances", status_code=status.HTTP_302_FOUND)
