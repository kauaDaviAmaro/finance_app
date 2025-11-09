from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.db.models import Base, User, WatchlistItem, PortfolioItem, Alert, TickerPrice
import logging
import traceback

# SQLAdmin imports
from sqladmin import Admin, ModelView

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

# Configuração de CORS - DEVE vir ANTES dos routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers para garantir CORS headers mesmo em erros
# Ordem: mais específicos primeiro

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# --- (Início) Registro dos Modelos no SQLAdmin ---

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username, User.role, User.is_active, User.created_at]
    column_searchable_list = [User.email, User.username]
    column_sortable_list = [User.id, User.email, User.username, User.role, User.is_active, User.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    icon = "fa-solid fa-user"


class PortfolioItemAdmin(ModelView, model=PortfolioItem):
    column_list = [PortfolioItem.id, PortfolioItem.ticker, PortfolioItem.user_id, PortfolioItem.quantity, PortfolioItem.purchase_price]
    column_searchable_list = [PortfolioItem.ticker]
    column_sortable_list = [PortfolioItem.id, PortfolioItem.ticker, PortfolioItem.user_id, PortfolioItem.quantity]
    can_create = True
    can_edit = True
    can_delete = True
    icon = "fa-solid fa-briefcase"


class WatchlistAdmin(ModelView, model=WatchlistItem):
    column_list = [WatchlistItem.id, WatchlistItem.ticker, WatchlistItem.user_id, WatchlistItem.created_at]
    column_searchable_list = [WatchlistItem.ticker]
    column_sortable_list = [WatchlistItem.id, WatchlistItem.ticker, WatchlistItem.user_id]
    can_create = True
    can_edit = True
    can_delete = True
    icon = "fa-solid fa-eye"


class AlertAdmin(ModelView, model=Alert):
    column_list = [Alert.id, Alert.ticker, Alert.user_id, Alert.indicator_type, Alert.is_active, Alert.triggered_at]
    column_searchable_list = [Alert.ticker, Alert.indicator_type]
    column_sortable_list = [Alert.id, Alert.ticker, Alert.user_id, Alert.is_active]
    can_create = True
    can_edit = True
    can_delete = True
    icon = "fa-solid fa-bell"


class TickerPriceAdmin(ModelView, model=TickerPrice):
    column_list = [TickerPrice.ticker, TickerPrice.last_price, TickerPrice.timestamp]
    column_searchable_list = [TickerPrice.ticker]
    column_sortable_list = [TickerPrice.ticker, TickerPrice.last_price, TickerPrice.timestamp]
    can_create = False
    can_edit = True
    can_delete = True
    icon = "fa-solid fa-dollar-sign"


# Monta o Admin
admin = Admin(app, engine)

# Adiciona as visualizações dos modelos
admin.add_view(UserAdmin)
admin.add_view(PortfolioItemAdmin)
admin.add_view(WatchlistAdmin)
admin.add_view(AlertAdmin)
admin.add_view(TickerPriceAdmin)

# --- (Fim) Registro dos Modelos no SQLAdmin ---

from app.routers import auth as auth_router
from app.routers import stock as stock_router
from app.routers import watchlist as watchlist_router
from app.routers import portfolio as portfolio_router
from app.routers import alert as alert_router
from app.routers import webhooks as webhooks_router
from app.routers import subscription as subscription_router

# Inclui as rotas
app.include_router(auth_router.router)
app.include_router(stock_router.router)
app.include_router(watchlist_router.router)
app.include_router(portfolio_router.router)
app.include_router(alert_router.router)
app.include_router(webhooks_router.router)
app.include_router(subscription_router.router)

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