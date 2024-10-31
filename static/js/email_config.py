from fastapi import FastAPI, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List

app = FastAPI()

class EmailSchema(BaseModel):
    email: List[EmailStr]
    subject: str
    body: str

conf = ConnectionConfig(
    MAIL_USERNAME = "tu_email@gmail.com",
    MAIL_PASSWORD = "tu_contraseña",
    MAIL_FROM = "tu_email@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True
)

@app.post("/send-email")
async def send_email(email: EmailSchema, background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject=email.subject,
        recipients=email.email,
        body=email.body,
        subtype="html"
    )
    
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return {"message": "Email has been sent"}