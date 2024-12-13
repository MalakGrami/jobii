import asyncio
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import torch
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
import fitz  # PyMuPDF for extracting PDF text

# Download NLTK stopwords
nltk.download('stopwords')



# Function to clean and preprocess text
def clean_text(text):
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    stop_words = set(stopwords.words('english'))
    return ' '.join(word for word in text.split() if word not in stop_words)

# Extract sections (Skills, Education, Experience) from the resume/job description
def extract_section(text, section_names):
    for section_name in section_names:
        match = re.search(rf'({section_name})\s*[:\n]*(.*?)(?=\n[^\w\s]|$)', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return ''

async def get_embedding(text, model_name="distilbert-base-uncased"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return embedding

def cosine_similarity_embeddings(emb1, emb2):
    if emb1 is None or emb2 is None:
        return 0
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return similarity if similarity >= 0 else 0


async def calculate_match(cv_text, job_text):
    cv_text_cleaned = clean_text(cv_text)
    job_text_cleaned = clean_text(job_text)

    section_names_skills = ["Skills", "Skill Details", "Tools"]
    section_names_education = [
        "Education", "Education Details", "Academic Qualifications", "Degrees", "Diplomas",
        "Educational Background", "Qualifications", "Training", "Certifications", "Academic History",
        "Scholarships", "Honors", "Courses", "Professional Development", "Licenses", "Degrees Earned",
        "Degree", "Diploma", "Training Programs", "Educational Attainment", "Graduation",
        "Certification Programs", "Academic Credentials", "Schooling", "Higher Education", "College",
        "University", "Postgraduate", "Undergraduate", "Bachelor", "Master", "PhD", "Associate Degree",
        "High School Diploma", "GCSE", "A-Level", "O-Level", "Vocational Training"
    ]
    section_names_experience = [
        "Experience", "Exprience", "Projects", "Company", "Work Details", "Employment History"
    ]

    # Extract sections for skills, education, and experience
    cv_skills = extract_section(cv_text_cleaned, section_names_skills)
    job_skills = extract_section(job_text_cleaned, section_names_skills)
    cv_education = extract_section(cv_text_cleaned, section_names_education)
    job_education = extract_section(job_text_cleaned, section_names_education)
    cv_experience = extract_section(cv_text_cleaned, section_names_experience)
    job_experience = extract_section(job_text_cleaned, section_names_experience)

    # Asynchronously get embeddings for skills, education, and experience
    embeddings = await asyncio.gather(
        get_embedding(cv_skills), get_embedding(job_skills),
        get_embedding(cv_education), get_embedding(job_education),
        get_embedding(cv_experience), get_embedding(job_experience)
    )

    # Unpack the embeddings list
    skills_embedding_cv, skills_embedding_job = embeddings[0], embeddings[1]
    education_embedding_cv, education_embedding_job = embeddings[2], embeddings[3]
    experience_embedding_cv, experience_embedding_job = embeddings[4], embeddings[5]

    # Calculate cosine similarity
    skills_similarity = cosine_similarity_embeddings(skills_embedding_cv, skills_embedding_job)
    education_similarity = cosine_similarity_embeddings(education_embedding_cv, education_embedding_job)
    experience_similarity = cosine_similarity_embeddings(experience_embedding_cv, experience_embedding_job)

    overall_match = (skills_similarity + education_similarity + experience_similarity) / 3
    return {
        "Skills Match (%)": f"{skills_similarity * 100:.2f}",
        "Education Match (%)": f"{education_similarity * 100:.2f}",
        "Experience Match (%)": f"{experience_similarity * 100:.2f}",
        "Overall Match (%)": f"{overall_match * 100:.2f}"
    }