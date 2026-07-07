import os
import secrets
import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import Watch, WatchImage
from .schemas import AiStubOut, LoginIn, WatchCreate, WatchImageOut, WatchOut, WatchUpdate
from .valuation import calculate_valuation

Base.metadata.create_all(bind=engine)
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="RastroWatch API")
serializer = URLSafeSerializer(settings.session_secret, salt="rastrowatch-session")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8085", "http://127.0.0.1:8085"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")


def require_auth(request: Request):
    token = request.cookies.get("rastrowatch_session")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        data = serializer.loads(token)
    except BadSignature as exc:
        raise HTTPException(status_code=401, detail="Sesión inválida") from exc
    if data.get("user") != settings.admin_user:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    return data


def image_out(image: WatchImage) -> WatchImageOut:
    return WatchImageOut(id=image.id, filename=image.filename, original_name=image.original_name, url=f"/uploads/{image.filename}")


def watch_out(watch: Watch) -> WatchOut:
    data = WatchOut.model_validate(watch)
    data.images = [image_out(image) for image in watch.images]
    return data


def apply_valuation(watch: Watch):
    valuation = calculate_valuation(watch.__dict__)
    watch.opportunity = valuation["opportunity"]
    watch.resale_margin = valuation["resale_margin"]
    watch.recommendation = valuation["recommendation"]
    watch.valuation_warning = valuation["valuation_warning"]


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "RastroWatch"}


@app.post("/api/login")
def login(payload: LoginIn, response: Response):
    if not (secrets.compare_digest(payload.username, settings.admin_user) and secrets.compare_digest(payload.password, settings.admin_password)):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = serializer.dumps({"user": settings.admin_user})
    response.set_cookie("rastrowatch_session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return {"ok": True, "user": settings.admin_user}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("rastrowatch_session")
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(require_auth)):
    return {"user": user["user"]}


@app.get("/api/watches", response_model=list[WatchOut])
def list_watches(db: Annotated[Session, Depends(get_db)], q: str = "", user=Depends(require_auth)):
    query = db.query(Watch).order_by(Watch.created_at.desc())
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(Watch.brand.ilike(pattern), Watch.model.ilike(pattern), Watch.reference.ilike(pattern), Watch.identification_notes.ilike(pattern), Watch.quick_notes.ilike(pattern)))
    return [watch_out(watch) for watch in query.all()]


@app.post("/api/watches", response_model=WatchOut)
def create_watch(payload: WatchCreate, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    watch = Watch(**payload.model_dump())
    apply_valuation(watch)
    db.add(watch)
    db.commit()
    db.refresh(watch)
    return watch_out(watch)


@app.get("/api/watches/{watch_id}", response_model=WatchOut)
def get_watch(watch_id: int, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    watch = db.get(Watch, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="Reloj no encontrado")
    return watch_out(watch)


@app.put("/api/watches/{watch_id}", response_model=WatchOut)
def update_watch(watch_id: int, payload: WatchUpdate, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    watch = db.get(Watch, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="Reloj no encontrado")
    for key, value in payload.model_dump().items():
        setattr(watch, key, value)
    apply_valuation(watch)
    db.commit()
    db.refresh(watch)
    return watch_out(watch)


@app.delete("/api/watches/{watch_id}")
def delete_watch(watch_id: int, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    watch = db.get(Watch, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="Reloj no encontrado")
    for image in watch.images:
        Path(settings.uploads_dir, image.filename).unlink(missing_ok=True)
    db.delete(watch)
    db.commit()
    return {"ok": True}


@app.post("/api/watches/{watch_id}/images", response_model=WatchImageOut)
def upload_image(watch_id: int, db: Annotated[Session, Depends(get_db)], file: UploadFile = File(...), user=Depends(require_auth)):
    watch = db.get(Watch, watch_id)
    if not watch:
        raise HTTPException(status_code=404, detail="Reloj no encontrado")
    ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    filename = f"{uuid4().hex}{ext}"
    destination = Path(settings.uploads_dir) / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    image = WatchImage(watch_id=watch.id, filename=filename, original_name=file.filename or "")
    db.add(image)
    db.commit()
    db.refresh(image)
    return image_out(image)


@app.post("/api/quick-seen", response_model=WatchOut)
def quick_seen(db: Annotated[Session, Depends(get_db)], brand: str = Form(""), model: str = Form(""), seen_price: float | None = Form(None), location: str = Form("otro"), quick_notes: str = Form(""), file: UploadFile | None = File(None), user=Depends(require_auth)):
    watch = Watch(brand=brand, model=model, seen_price=seen_price, location=location, quick_notes=quick_notes, status="pendiente de investigar", condition="sin probar", recommendation="investigar más")
    apply_valuation(watch)
    db.add(watch)
    db.commit()
    db.refresh(watch)
    if file:
        ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
        filename = f"{uuid4().hex}{ext}"
        with (Path(settings.uploads_dir) / filename).open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        db.add(WatchImage(watch_id=watch.id, filename=filename, original_name=file.filename or ""))
        db.commit()
        db.refresh(watch)
    return watch_out(watch)


@app.post("/api/ai/analyze", response_model=AiStubOut)
def ai_analyze(user=Depends(require_auth)):
    return AiStubOut(message="IA pendiente de configurar")
