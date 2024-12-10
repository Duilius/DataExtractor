from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Usa el objeto `templates` configurado previamente
templates = Jinja2Templates(directory="templates")


area_router = APIRouter()

@area_router.get("/get-area-nombre/{area_id}")
async def get_area_nombre(area_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT nombre FROM areas_oficiales WHERE id = :area_id"),
        {"area_id": area_id}
    ).first()
    return result[0] if result else ""

@area_router.get("/areas-oficiales", response_class=HTMLResponse)
async def get_areas_oficiales(request:Request,db: Session = Depends(get_db)):
    result = db.execute(text("SELECT id, nombre FROM areas_oficiales ORDER BY id")).fetchall()
    areas_oficiales = [{"id": row[0], "nombre": row[1]} for row in result]
    
    return templates.TemplateResponse(
        "datos_inventario_OK.html", 
        {"request": request, "areas_oficiales": areas_oficiales}
    )