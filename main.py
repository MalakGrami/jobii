from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.controllers.UserController import router as user_router
from app.controllers.CompanyController import router as company_router

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Registering the user and company routes
app.include_router(user_router, prefix="/user")
app.include_router(company_router, prefix="/company")
