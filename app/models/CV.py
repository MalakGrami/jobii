from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.database import Base 

class CV(Base):
    __tablename__ = 'cvs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cv_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
