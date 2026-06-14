from datetime import date
from fastapi import APIRouter, Depends, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User, Group, GroupMember
from auth import get_current_user

router = APIRouter(prefix="/groups", tags=["Groups"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def list_groups(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all groups the current user belongs to."""
    # Find all active group memberships for the user
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id,
        (GroupMember.left_at == None) | (GroupMember.left_at > date.today())
    ).all()
    
    groups = [m.group for m in memberships]
    
    return templates.TemplateResponse(
        "groups.html", 
        {"request": request, "user": current_user, "groups": groups}
    )


@router.post("", response_class=HTMLResponse)
async def create_group(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new group and add the creator as the first member."""
    new_group = Group(name=name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    # Auto-add creator as first member
    first_member = GroupMember(
        group_id=new_group.id,
        user_id=current_user.id,
        joined_at=date.today()
    )
    db.add(first_member)
    db.commit()
    
    return RedirectResponse(url=f"/groups/{new_group.id}", status_code=status.HTTP_302_FOUND)


@router.get("/{group_id}", response_class=HTMLResponse)
async def group_detail(
    request: Request, 
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Show group details and its members."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Verify current user is a member of this group
    is_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not is_member:
        return RedirectResponse(url="/groups", status_code=status.HTTP_302_FOUND)
        
    # Fetch all members of this group
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    # Check if current user is the creator (first member added)
    first_member_id = db.query(GroupMember).filter(GroupMember.group_id == group_id).order_by(GroupMember.id.asc()).first()
    is_creator = first_member_id and first_member_id.user_id == current_user.id
    
    return templates.TemplateResponse(
        "group_detail.html", 
        {
            "request": request, 
            "user": current_user, 
            "group": group, 
            "members": members,
            "is_creator": is_creator
        }
    )


@router.post("/{group_id}/delete")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a group (only creator can do this). We use POST because standard HTML forms don't support DELETE method natively."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Check if creator
    first_member = db.query(GroupMember).filter(GroupMember.group_id == group_id).order_by(GroupMember.id.asc()).first()
    if not first_member or first_member.user_id != current_user.id:
        # Not authorized
        return RedirectResponse(url=f"/groups/{group_id}", status_code=status.HTTP_302_FOUND)
        
    db.delete(group) # SQLAlchemy cascade handles group_members, expenses etc.
    db.commit()
    
    return RedirectResponse(url="/groups", status_code=status.HTTP_302_FOUND)
