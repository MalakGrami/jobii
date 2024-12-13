from sqlalchemy import Column, Integer, Float, ForeignKey
from app.database.database import Base 
class Match(Base):
    __tablename__ = 'match'
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    cv_id = Column(Integer, ForeignKey('cvs.id'))
    skills_match = Column(Float, nullable=True)  
    education_match = Column(Float, nullable=True)  
    experience_match = Column(Float, nullable=True)  
    match_percent = Column(Float, nullable=True) 
    
