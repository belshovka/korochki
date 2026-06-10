from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Annotated

users = []
records = []

class NewUser(BaseModel):
    name: str
    password: str
    age: int

class AuthUser(BaseModel):
    name: str
    password: str

class NewRecord(BaseModel):
    course: str
    date: str
    payment: str

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"))
templates = Jinja2Templates("templates")

@app.get("/")
def root_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/login")
def login_page(request: Request):
    if request.cookies.get("name"):
        return RedirectResponse("/records", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "heading": "Вход"
        }
    )

@app.post("/login")
def login(request: Request, user: Annotated[AuthUser, Form()]):
    found_user = {}
    for u in users:
        if u.name == user.name:
            found_user = u
            break
    
    if not found_user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Пользователь не найден",
                "heading": "Попробуйте снова"
            }
        )

    if found_user.password == user.password:
        response = RedirectResponse("/records", status_code=302)
        response.set_cookie("name", user.name)
        return response
    
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": "Неверный пароль",
            "heading": "Попробуйте снова"
        }
    )

@app.get("/register")
def register_page(request: Request):
    if request.cookies("name"):
        return RedirectResponse("/records", status_code=302)
    
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "heading": "Регистрация"
        }
    )

@app.post("/register")
def add_user(user: Annotated[NewUser, Form()]):
    users.append(user)
    return RedirectResponse("/login", status_code=302)

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("name")
    return response

@app.get("/create")
def create_record_page(request: Request):
    if not request.cookies.get("name"):
        return RedirectResponse("/records", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="new_record.html"
    )

@app.post("/create")
def add_record(record: Annotated[NewRecord, Form()]):
    records.append(record)
    return RedirectResponse("/records", status_code=302)

@app.get("/records")
def records_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="records.html",
        context={
            "records": records
        }
    )