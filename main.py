import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import clientes, export, items, pagos, pedidos, publico, stats
from routers.auth import get_current_user, router as auth_router

app = FastAPI(title="Facturador Temu", version="1.0.0", redirect_slashes=False)

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
    return {"status": "ok", "message": "Facturador Temu API"}
