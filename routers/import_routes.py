import json
from fastapi import APIRouter, Depends, Request, UploadFile, File, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User, Group, ImportLog
from auth import get_current_user
from utils.csv_parser import process_csv_import

router = APIRouter(tags=["Import"])
templates = Jinja2Templates(directory="templates")

@router.get("/groups/{group_id}/import", response_class=HTMLResponse)
async def import_page(
    request: Request, 
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Render the CSV import upload page."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    return templates.TemplateResponse(request=request, name="import.html", context= 
        {"request": request, "user": current_user, "group": group}
    )


@router.post("/groups/{group_id}/import")
async def process_import(
    request: Request,
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process the uploaded CSV file, run the parser, and save the report."""
    # Ensure it's a CSV file
    if not file.filename.endswith(".csv"):
        # Should flash an error, but simple redirect for now
        return RedirectResponse(url=f"/groups/{group_id}/import", status_code=status.HTTP_302_FOUND)
        
    # Read file content
    content = await file.read()
    decoded_content = content.decode("utf-8-sig")
    
    # Run the core parsing pipeline
    report = process_csv_import(decoded_content, group_id, db)
    
    # Save the import log to the database for auditing
    log_record = ImportLog(
        group_id=group_id,
        filename=file.filename,
        total_rows=report["total_rows"],
        imported=report["imported"],
        flagged=report["flagged"],
        skipped=report["skipped"],
        report_json=json.dumps(report["anomalies"])
    )
    db.add(log_record)
    db.commit()
    db.refresh(log_record)
    
    # Redirect to the report view
    return RedirectResponse(url=f"/import/report/{log_record.id}", status_code=status.HTTP_302_FOUND)


@router.get("/import/report/{log_id}", response_class=HTMLResponse)
async def import_report_page(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Display the results and anomalies of an import."""
    log_record = db.query(ImportLog).filter(ImportLog.id == log_id).first()
    if not log_record:
        raise HTTPException(status_code=404, detail="Import Log not found")
        
    group = db.query(Group).filter(Group.id == log_record.group_id).first()
    anomalies = json.loads(log_record.report_json) if log_record.report_json else []
    
    return templates.TemplateResponse(request=request, name="import_report.html", context= 
        {
            "request": request, 
            "user": current_user, 
            "group": group,
            "log": log_record,
            "anomalies": anomalies
        }
    )
