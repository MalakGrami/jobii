from sqlalchemy import Column, Integer, Text
from app.database.database import Base 

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, index=True)
    job_description = Column(Text, nullable=False)
