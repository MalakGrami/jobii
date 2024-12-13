import os  # To handle file paths
from sqlalchemy.orm import Session  # For database operations
from app.database.database import SessionLocal  # Assuming this is where you defined the SessionLocal
from app.models.CV import CV  # CV model
from app.models.Job import Job  # Job model
from app.models.Match import Match  # Match model
from fastapi import APIRouter, UploadFile, Form, Request, Depends  # FastAPI dependencies
from app.services.file_service import extract_pdf_text  # Function to extract text from PDF
from app.services.nlp_service import calculate_match  # NLP function to calculate the match
from fastapi.templating import Jinja2Templates  # For rendering HTML templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/users/upload-cv/")
async def get_upload_cv_form(request: Request):
    """Display the form for the user to upload their CV."""
    return templates.TemplateResponse("user.html", {"request": request})


@router.post("/upload-cv/")
async def upload_cv(
    request: Request, 
    cv: UploadFile, 
    db: Session = Depends(get_db)
):
    """Handles CV upload, saves it in the database, and calculates match with all jobs."""
    try:
        # 1️⃣ Save the uploaded CV file
        base_path = os.path.join(os.path.dirname(__file__), "../cv_files/")
        os.makedirs(base_path, exist_ok=True)  # Ensure the directory exists
        cv_path = os.path.join(base_path, cv.filename)

        with open(cv_path, "wb") as f:
            f.write(await cv.read())

        # 2️⃣ Store CV information in the database
        new_cv = CV(cv_path=cv_path)
        db.add(new_cv)
        db.commit()
        db.refresh(new_cv)  # Get the newly created CV's ID

        # 3️⃣ Extract text from the CV and calculate match for all jobs
        cv_text = extract_pdf_text(cv_path)
        jobs = db.query(Job).all()  # Retrieve all jobs from the database

        match_results = []
        for job in jobs:
            # Check if this CV-job match already exists in the Match table
            existing_match = db.query(Match).filter(Match.cv_id == new_cv.id, Match.job_id == job.id).first()

            if existing_match:
                match_results.append({
                    "job_id": job.id,
                    "job_description": job.job_description,
                    "skills_match": existing_match.skills_match,
                    "education_match": existing_match.education_match,
                    "experience_match": existing_match.experience_match,
                    "overall_match": existing_match.match_percent,
                    "status": "Already calculated"
                })
            else:
                # Calculate match if no existing match is found
                match_result = await calculate_match(cv_text, job.job_description)
                
                # Extract the match percentages for Skills, Education, Experience, and Overall
                skills_match = float(match_result["Skills Match (%)"].replace('%', ''))
                education_match = float(match_result["Education Match (%)"].replace('%', ''))
                experience_match = float(match_result["Experience Match (%)"].replace('%', ''))
                overall_match = float(match_result["Overall Match (%)"].replace('%', ''))

                # Store the match information in the Match table
                new_match = Match(
                    job_id=job.id, 
                    cv_id=new_cv.id, 
                    match_percent=overall_match, 
                    skills_match=skills_match, 
                    education_match=education_match, 
                    experience_match=experience_match
                )
                db.add(new_match)
                db.commit()

                match_results.append({
                    "job_id": job.id,
                    "job_description": job.job_description,
                    "skills_match": skills_match,
                    "education_match": education_match,
                    "experience_match": experience_match,
                    "overall_match": overall_match,
                    "status": "Newly calculated"
                })

        # 4️⃣ Sort match results by 'overall_match' in descending order
        match_results = sorted(match_results, key=lambda x: x['overall_match'], reverse=True)

        return templates.TemplateResponse("user.html", {
            "request": request, 
            "cv_path": new_cv.cv_path, 
            "match_results": match_results
        })

    except Exception as e:
        db.rollback()
        print(f"Error processing the CV: {e}")
        return templates.TemplateResponse("user.html", {"request": request, "error": "An error occurred while processing your CV."})
    
    finally:
        db.close()  # Ensure the database session is closed
