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
    
    return templates.TemplateResponse(request=request, name="groups.html", context= 
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
    
    return templates.TemplateResponse(request=request, name="group_detail.html", context= 
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


# --- Step 4.1.2: Member Management Routes ---

@router.post("/{group_id}/members")
async def add_member(
    request: Request,
    group_id: int,
    user_email: str = Form(...),
    joined_at: date = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new member to the group."""
    # Find user by email
    target_user = db.query(User).filter(User.email == user_email).first()
    if not target_user:
        # In a real app we might return an error template, but for now redirect with query param or just simple response
        # Using a simple HTTP exception for simplicity, though flash messages are better in UI
        return HTMLResponse("User with this email not found.", status_code=400)
        
    # Check if they are already active in the group
    existing_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == target_user.id,
        GroupMember.left_at == None  # Currently active
    ).first()
    
    if existing_membership:
        return HTMLResponse("User is already an active member of this group.", status_code=400)
        
    # Add member
    new_member = GroupMember(
        group_id=group_id,
        user_id=target_user.id,
        joined_at=joined_at
    )
    db.add(new_member)
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group_id}", status_code=status.HTTP_302_FOUND)


@router.post("/{group_id}/members/{user_id}/leave")
async def set_leave_date(
    request: Request,
    group_id: int,
    user_id: int,
    left_at: date = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set the date a member left the group (using POST for HTML form support)."""
    # Find the active membership
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.left_at == None
    ).first()
    
    if not membership:
        return HTMLResponse("Active membership not found.", status_code=404)
        
    # Validate leave date > join date
    if left_at <= membership.joined_at:
        return HTMLResponse("Leave date must be after join date.", status_code=400)
        
    # Set leave date
    membership.left_at = left_at
    db.commit()
    
    return RedirectResponse(url=f"/groups/{group_id}", status_code=status.HTTP_302_FOUND)


@router.get("/{group_id}/members")
async def list_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List members with join/leave dates (API endpoint)."""
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    # Return JSON representation since this is an API list
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "name": m.user.name,
            "email": m.user.email,
            "joined_at": m.joined_at,
            "left_at": m.left_at
        }
        for m in members
    ]
