from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User, Group, GroupMember
from auth import get_current_user
from utils.balance_engine import compute_net_balances, simplify_debts

router = APIRouter(tags=["Balances"])
templates = Jinja2Templates(directory="templates")

@router.get("/groups/{group_id}/balances", response_class=HTMLResponse)
async def view_balances(
    request: Request, 
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """View the simplified debt balances for a group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Get all members for displaying names
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    user_map = {m.user_id: m.user for m in members}
    
    # Calculate who owes whom
    net_balances = compute_net_balances(group_id, db)
    transactions = simplify_debts(net_balances)
    
    # Map the transactions to rich objects for the template
    simplified_debts = []
    for from_id, to_id, amount in transactions:
        simplified_debts.append({
            "from_user": user_map.get(from_id),
            "to_user": user_map.get(to_id),
            "amount": amount
        })
        
    # Also pass raw net balances so users can see their exact +/- position
    rich_net_balances = []
    for uid, bal in net_balances.items():
        if bal != 0:
            rich_net_balances.append({
                "user": user_map.get(uid),
                "balance": bal
            })
            
    # Sort net balances: creditors (positive) first, debtors (negative) last
    rich_net_balances.sort(key=lambda x: x["balance"], reverse=True)
    
    return templates.TemplateResponse(request=request, name="balances.html", context= 
        {
            "request": request, 
            "user": current_user, 
            "group": group, 
            "debts": simplified_debts,
            "net_balances": rich_net_balances
        }
    )
