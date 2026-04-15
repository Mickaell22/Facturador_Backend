from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import clientes, items, pagos, pedidos, stats
from routers.auth import get_current_user, router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Facturador Temu", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth sin proteccion (es el endpoint de login/callback)
app.include_router(auth_router)

# Todos los demas requieren JWT valido
_auth = [Depends(get_current_user)]
app.include_router(clientes.router, dependencies=_auth)
app.include_router(pedidos.router, dependencies=_auth)
app.include_router(items.router, dependencies=_auth)
app.include_router(pagos.router, dependencies=_auth)
app.include_router(stats.router, dependencies=_auth)


@app.get("/")
def root():
    return {"status": "ok", "message": "Facturador Temu API"}
