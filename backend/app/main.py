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

# --- Automatic watch investigator / estimator endpoints ---
from .models import WatchInvestigation
from .schemas import AIWatchAnalysis, PriceSearchIn, PriceSearchOut, WatchInvestigationOut, WatchInvestigationPatch
from .services.ai.watch_identifier import WatchIdentifier
from .services.storage.image_storage import save_upload, upload_path
from .services.valuation.price_aggregator import PriceAggregator, source_status
from .services.valuation.valuation_engine import ValuationEngine



def external_price_sources_configured() -> bool:
    status = source_status()
    return any(status.get(key) for key in ("ebay", "thewatchapi", "watchcharts", "wallapop_apify", "milanuncios_apify", "catawiki_apify"))


def ai_only_valuation(analysis: AIWatchAnalysis, price_seen: float | None = None) -> ValuationResult:
    warnings = list(analysis.warnings or [])
    warnings.insert(0, "Estimación IA pendiente de validar con fuentes externas.")
    if not any([analysis.market_value_initial_estimate, analysis.current_real_value_estimate_median, analysis.recommended_buy_price, analysis.probable_sale_value]):
        warnings.append("Datos insuficientes: OpenAI no devolvió una estimación numérica fiable.")

    median_value = analysis.current_real_value_estimate_median
    recommended = analysis.recommended_buy_price
    high = analysis.current_real_value_estimate_high or median_value
    recommendation = analysis.recommendation or "investigar más"
    opportunity = "datos insuficientes"
    if price_seen is not None and recommended is not None and median_value is not None:
        if price_seen <= recommended * 0.75:
            opportunity = "muy buena"
            warnings.append("Precio muy por debajo de la estimación IA: revisar autenticidad y estado antes de comprar.")
        elif price_seen <= recommended:
            opportunity = "buena"
        elif price_seen <= median_value:
            opportunity = "negociable"
        elif high is not None and price_seen > high:
            opportunity = "mala"
            recommendation = "evitar"
        else:
            opportunity = "caro"
            recommendation = "negociar"
    elif median_value is not None:
        opportunity = "estimación IA"

    if analysis.authenticity_risk == "alto":
        warnings.append("Riesgo alto de falsificación: validar manualmente antes de comprar.")
        recommendation = "investigar más / evitar"

    return ValuationResult(
        market_value_initial=analysis.market_value_initial_estimate,
        current_real_value_low=analysis.current_real_value_estimate_low,
        current_real_value_median=median_value,
        current_real_value_high=analysis.current_real_value_estimate_high,
        recommended_buy_price=recommended,
        probable_sale_value=analysis.probable_sale_value,
        resale_margin=analysis.resale_margin if analysis.resale_margin is not None else ((analysis.probable_sale_value - price_seen) if price_seen is not None and analysis.probable_sale_value is not None else None),
        opportunity=opportunity,
        recommendation=recommendation,
        warnings=warnings,
        sources_used=["OpenAI Vision (estimación sin validar)"],
        confidence=analysis.confidence,
        results=[],
    )

def investigation_out(investigation: WatchInvestigation) -> WatchInvestigationOut:
    data = WatchInvestigationOut.model_validate(investigation)
    data.uploaded_image_url = f"/uploads/{investigation.uploaded_image_path}"
    return data


def analysis_queries(analysis) -> list[str]:
    queries = list(analysis.search_queries or [])
    main_query = " ".join(filter(None, [analysis.brand, analysis.model, analysis.reference]))
    if main_query and main_query not in queries:
        queries.insert(0, main_query)
    return queries


@app.get("/api/sources/status")
def get_sources_status(user=Depends(require_auth)):
    status = source_status()
    status["openai"] = bool(settings.openai_api_key)
    return status


@app.post("/api/watch/identify", response_model=AIWatchAnalysis)
async def identify_watch(image: UploadFile = File(...), user=Depends(require_auth)):
    filename = await save_upload(image, prefix="identify")
    analysis = await WatchIdentifier().identify(upload_path(filename))
    return analysis


@app.post("/api/price-search", response_model=PriceSearchOut)
async def price_search(payload: PriceSearchIn, user=Depends(require_auth)):
    results = await PriceAggregator().search([payload.query], payload.source_filters)
    valuation = ValuationEngine().calculate(results, price_seen=payload.price_seen)
    return PriceSearchOut(results=results, valuation=valuation)


@app.post("/api/watch/analyze-full", response_model=WatchInvestigationOut)
async def analyze_full(db: Annotated[Session, Depends(get_db)], image: UploadFile = File(...), price_seen: float | None = Form(None), location_seen: str = Form("otro"), notes: str = Form(""), user=Depends(require_auth)):
    filename = await save_upload(image, prefix="analysis")
    analysis = await WatchIdentifier().identify(upload_path(filename))
    queries = analysis_queries(analysis)
    if not queries:
        queries = ["reloj segunda mano"]
    if external_price_sources_configured():
        results = await PriceAggregator().search(queries[:4])
        valuation = ValuationEngine().calculate(results, analysis=analysis, price_seen=price_seen)
    else:
        valuation = ai_only_valuation(analysis, price_seen=price_seen)
    investigation = WatchInvestigation(
        uploaded_image_path=filename,
        user_price_seen=price_seen,
        user_location_seen=location_seen,
        user_notes=notes,
        ai_analysis=analysis.model_dump(),
        valuation_result=valuation.model_dump(),
        selected_brand=analysis.brand,
        selected_model=analysis.model,
        selected_reference=analysis.reference,
        final_status="pendiente",
        manual_corrections={},
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return investigation_out(investigation)


@app.get("/api/watch/investigations", response_model=list[WatchInvestigationOut])
def list_investigations(db: Annotated[Session, Depends(get_db)], status: str = "", user=Depends(require_auth)):
    query = db.query(WatchInvestigation).order_by(WatchInvestigation.created_at.desc())
    if status:
        query = query.filter(WatchInvestigation.final_status == status)
    return [investigation_out(item) for item in query.all()]


@app.get("/api/watch/investigations/{investigation_id}", response_model=WatchInvestigationOut)
def get_investigation(investigation_id: int, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    investigation = db.get(WatchInvestigation, investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigación no encontrada")
    return investigation_out(investigation)


@app.patch("/api/watch/investigations/{investigation_id}", response_model=WatchInvestigationOut)
def patch_investigation(investigation_id: int, payload: WatchInvestigationPatch, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    investigation = db.get(WatchInvestigation, investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigación no encontrada")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(investigation, key, value)
    db.commit()
    db.refresh(investigation)
    return investigation_out(investigation)


@app.post("/api/watch/investigations/{investigation_id}/validate", response_model=WatchInvestigationOut)
def validate_investigation(investigation_id: int, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    investigation = db.get(WatchInvestigation, investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigación no encontrada")
    investigation.final_status = "validado"
    db.commit()
    db.refresh(investigation)
    return investigation_out(investigation)


@app.post("/api/watch/investigations/{investigation_id}/save-as-watch", response_model=WatchOut)
def save_investigation_as_watch(investigation_id: int, db: Annotated[Session, Depends(get_db)], user=Depends(require_auth)):
    investigation = db.get(WatchInvestigation, investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigación no encontrada")
    analysis = investigation.ai_analysis or {}
    valuation = investigation.valuation_result or {}
    watch = Watch(
        brand=investigation.selected_brand or analysis.get("brand") or "",
        model=investigation.selected_model or analysis.get("model") or "",
        reference=investigation.selected_reference or analysis.get("reference") or "",
        movement_type=analysis.get("movement") or "desconocido",
        condition=analysis.get("detected_condition") or "desconocido",
        estimated_min_price=valuation.get("current_real_value_low"),
        estimated_avg_price=valuation.get("current_real_value_median"),
        estimated_max_price=valuation.get("current_real_value_high"),
        recommended_buy_price=valuation.get("recommended_buy_price"),
        seen_price=investigation.user_price_seen,
        resale_margin=valuation.get("resale_margin"),
        counterfeit_risk=analysis.get("authenticity_risk") or "medio",
        price_reliability="alta" if valuation.get("confidence", 0) >= 0.7 else "media" if valuation.get("confidence", 0) >= 0.4 else "baja",
        identification_notes=analysis.get("notes") or "",
        prebuy_checklist="\n".join(valuation.get("warnings", [])),
        price_sources=", ".join(valuation.get("sources_used", [])),
        location=investigation.user_location_seen or "otro",
        quick_notes=investigation.user_notes or "",
        status="investigado",
    )
    apply_valuation(watch)
    db.add(watch)
    db.commit()
    db.refresh(watch)
    db.add(WatchImage(watch_id=watch.id, filename=investigation.uploaded_image_path, original_name="imagen de investigación"))
    investigation.final_status = "validado"
    db.commit()
    db.refresh(watch)
    return watch_out(watch)
