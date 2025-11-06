from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.database import engine
from app.db.models import Base
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tenta criar as tabelas no banco de dados (opcional)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables: {e}")
    logger.info("Application will start without database connection")

app = FastAPI(
    title="Finances API",
    description="API para gerenciamento de finanças pessoais",
    version="1.0.0"
)

# Adiciona esquema de autenticação Bearer ao OpenAPI (para aparecer o "Authorize" no Swagger)
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    security_schemes = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    components = openapi_schema.setdefault("components", {})
    existing_schemes = components.setdefault("securitySchemes", {})
    existing_schemes.update(security_schemes)
    # Se quiser exigir auth por padrão, descomente a linha abaixo
    # openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import auth as auth_router
from app.routers import stock as stock_router
from app.routers import watchlist as watchlist_router
from app.routers import portfolio as portfolio_router
from app.routers import alert as alert_router

# Inclui as rotas
app.include_router(auth_router.router)
app.include_router(stock_router.router)
app.include_router(watchlist_router.router)
app.include_router(portfolio_router.router)
app.include_router(alert_router.router)

@app.get("/health")
def health_check():
    # Verifica se o banco de dados está disponível
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status
    }