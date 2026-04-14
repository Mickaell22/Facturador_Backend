from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import clientes, pedidos, items, pagos

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Facturador Temu", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes.router)
app.include_router(pedidos.router)
app.include_router(items.router)
app.include_router(pagos.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Facturador Temu API"}
