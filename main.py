import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from routers import clientes, export, items, pagos, pedidos, publico, stats
from routers.auth import get_current_user, router as auth_router
from routers.publico import og_preview

app = FastAPI(title="Facturador", version="1.0.0", redirect_slashes=False)

_frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sin proteccion: login/callback y facturas publicas
app.include_router(auth_router)
app.include_router(publico.router)

# Todos los demas requieren JWT valido
_auth = [Depends(get_current_user)]
app.include_router(clientes.router, dependencies=_auth)
app.include_router(pedidos.router, dependencies=_auth)
app.include_router(items.router, dependencies=_auth)
app.include_router(pagos.router, dependencies=_auth)
app.include_router(stats.router, dependencies=_auth)
app.include_router(export.router, dependencies=_auth)


@app.get("/")
def root():
    return {"status": "ok", "message": "Facturador API"}


@app.get("/p/{token}", response_class=HTMLResponse)
def og_preview_root(token: str, db: Session = Depends(get_db)):
    return og_preview(token, db)
