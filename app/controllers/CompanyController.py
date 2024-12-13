from fastapi import APIRouter, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.Job import Job
from app.models.CV import CV
from app.models.Match import Match
from app.database.database import SessionLocal
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.services.nlp_service import calculate_match
from app.services.file_service import *

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/company/create-job/")
async def get_create_job_form(request: Request):
    return templates.TemplateResponse("company.html", {"request": request})


@router.post("/create-job/")
async def create_job(
    request: Request, 
    job_description: str = Form(...), 
    db: Session = Depends(get_db)
):
    # 1. Save the new job in the database
    new_job = Job(job_description=job_description)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # 2. Retrieve all CVs from the database
    cvs = db.query(CV).all()

    # 3. Calculate match for each CV
    match_results = []
    for cv in cvs:
        existing_match = db.query(Match).filter(Match.cv_id == cv.id, Match.job_id == new_job.id).first()
        if existing_match:
            match_results.append({
                "cv_id": cv.id,
                "cv_path": cv.cv_path,
                "skills_match": existing_match.skills_match,
                "education_match": existing_match.education_match,
                "experience_match": existing_match.experience_match,
                "match_percent": existing_match.match_percent,
                "status": "Already calculated"
            })
        else:
            # Extract the text from the CV file
            cv_text = extract_pdf_text(cv.cv_path)
            
            # Calculate the match details using the NLP service
            match_result = await calculate_match(cv_text, job_description)
            
            # Parse the individual match percentages
            skills_match = float(match_result["Skills Match (%)"].replace('%', ''))
            education_match = float(match_result["Education Match (%)"].replace('%', ''))
            experience_match = float(match_result["Experience Match (%)"].replace('%', ''))
            match_percent = float(match_result["Overall Match (%)"].replace('%', ''))

            # Create a new match entry in the database
            new_match = Match(
                job_id=new_job.id, 
                cv_id=cv.id, 
                skills_match=skills_match,
                education_match=education_match,
                experience_match=experience_match,
                match_percent=match_percent
            )
            db.add(new_match)
            db.commit()

            match_results.append({
                "cv_id": cv.id,
                "cv_path": cv.cv_path,
                "skills_match": skills_match,
                "education_match": education_match,
                "experience_match": experience_match,
                "match_percent": match_percent,
                "status": "Newly calculated"
            })

    # 4. Sort match results by 'match_percent' in descending order
    match_results = sorted(match_results, key=lambda x: x['match_percent'], reverse=True)

    # No need to close db, as FastAPI will handle it via `get_db()`
    return templates.TemplateResponse("company.html", {
        "request": request, 
        "job": new_job, 
        "match_results": match_results
    })
