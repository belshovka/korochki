from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from typing import Annotated
from sqlmodel import Field, SQLModel, create_engine, Session, select

class NewUser(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    login: str = Field(unique=True)
    password: str
    full_name: str
    phone: str
    email: str

class Record(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    course: str
    date: str
    payment: str
    status: str
    review: str | None = Field(default=None)
    user_id: int = Field(foreign_key="newuser.id")

class AuthUser(SQLModel):
    login: str
    password: str

class NewRecord(SQLModel):
    course: str
    date: str
    payment: str

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"))
templates = Jinja2Templates("templates")
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/korochki-belshov"
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(bind=engine)

@app.get("/")
def root_page(request: Request):
    if request.cookies.get("login") == "admin":
        return RedirectResponse("/admin", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/login")
def login_page(request: Request):
    if request.cookies.get("login") == "admin":
        return RedirectResponse("/admin", status_code=302)

    if request.cookies.get("login"):
        return RedirectResponse("/records", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "heading": "Вход"
        }
    )

@app.post("/login")
def get_user(request: Request, user: Annotated[AuthUser, Form()]):
    with Session(bind=engine) as session:
        found_user = session.exec(
            select(NewUser)
            .where(NewUser.login == user.login)
            .where(NewUser.password == user.password)
        ).one_or_none()
    
    if not found_user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Неверные данные",
                "heading": "Попробуйте снова"
            }
        )

    response = RedirectResponse("/records", status_code=302)
    response.set_cookie("login", user.login)
    response.set_cookie("user_id", found_user.id)
    return response

@app.get("/register")
def register_page(request: Request):
    if request.cookies.get("login") == "admin":
        return RedirectResponse("/admin", status_code=302)

    if request.cookies.get("login"):
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "heading": "Регистрация"
        }
    )

@app.post("/register")
def add_user(request: Request, user: Annotated[NewUser, Form()]):
    with Session(bind=engine) as session:
        try:
            session.add(user)
            session.commit()
        except IntegrityError:
            session.rollback()
            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={
                    "heading": "Регистрация",
                    "error": "Этот логин уже занят"
                }
            )

    return RedirectResponse("/login", status_code=302)

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("login")
    response.delete_cookie("user_id")
    return response

@app.get("/create")
def create_record_page(request: Request):
    if request.cookies.get("login") == "admin":
        return RedirectResponse("/admin", status_code=302)

    if not request.cookies.get("login"):
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="new_record.html"
    )

@app.post("/create")
def add_record(request: Request, record: Annotated[NewRecord, Form()]):
    user_id = request.cookies.get("user_id")

    with Session(bind=engine) as session:
        session.add(Record(
            course=record.course,
            date=record.date,
            payment=record.payment,
            status="Новая",
            user_id=user_id
        ))
        session.commit()
    return RedirectResponse("/records", status_code=302)

@app.get("/records")
def records_page(request: Request):
    if request.cookies.get("login") == "admin":
        return RedirectResponse("/admin", status_code=302)

    user_id = request.cookies.get("user_id")
    if not request.cookies.get("login"):
        return RedirectResponse("/", status_code=302)

    with Session(bind=engine) as session:
        user_records = session.exec(
            select(Record)
            .where(Record.user_id == user_id)
        ).all()
    
    return templates.TemplateResponse(
        request=request,
        name="records.html",
        context={
            "records": user_records
        }
    )

@app.get("/admin")
def admin_page(request: Request):
    if request.cookies.get("login") != "admin":
        return RedirectResponse("/", status_code=302)

    with Session(bind=engine) as session:
        all_records = session.exec(
            select(Record, NewUser)
            .where(Record.user_id == NewUser.id)
            .order_by(Record.id)).all()
        
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "records": all_records,
        }
    )

@app.post("/records/{id}")
def edit_record(request: Request, id: int, status: Annotated[str, Form()]):
    if request.cookies.get("login") != "admin":
        return RedirectResponse("/", status_code=302)

    with Session(bind=engine) as session:
        found_record = session.exec(
            select(Record)
            .where(Record.id == id)
        ).one()
        found_record.status = status
        session.add(found_record)
        session.commit()

    return RedirectResponse("/admin", status_code=302)