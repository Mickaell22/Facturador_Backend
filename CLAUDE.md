# Backend — FastAPI

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Railway)
- Cloudinary (imagenes)

## Estructura
```
backend/
├── main.py              # app FastAPI, CORS, registro de routers
├── database.py          # engine, SessionLocal, Base, get_db
├── models.py            # modelos ORM (tablas)
├── schemas.py           # esquemas Pydantic (request/response)
├── Procfile             # comando de inicio para Railway
├── requirements.txt
├── .env                 # credenciales locales (no se sube)
├── .env.example         # plantilla sin valores reales
├── routers/
│   ├── clientes.py      # CRUD clientes + aliases
│   ├── pedidos.py       # CRUD pedidos + agregar/quitar clientes
│   ├── items.py         # CRUD items + subida de imagen
│   ├── pagos.py         # CRUD pagos + subida de comprobante
│   └── stats.py         # estadisticas dashboard + historial por cliente
└── utils/
    └── cloudinary_helper.py  # upload_image(), delete_image()
```

## Endpoints disponibles

### Clientes
- GET/POST `/clientes`
- GET/PUT/DELETE `/clientes/{id}`
- POST/DELETE `/clientes/{id}/aliases`
- POST `/clientes/{id}/aliases/{alias_id}`

### Pedidos
- GET/POST `/pedidos`
- GET/PUT/DELETE `/pedidos/{id}`
- POST/DELETE `/pedidos/{id}/clientes/{cliente_id}`

### Items (por pedido-cliente)
- GET/POST `/pedido-clientes/{pc_id}/items`
- PUT/DELETE `/pedido-clientes/{pc_id}/items/{item_id}`
- POST `/pedido-clientes/{pc_id}/items/{item_id}/imagen`

### Pagos (por pedido-cliente)
- GET/POST `/pedido-clientes/{pc_id}/pagos`
- DELETE `/pedido-clientes/{pc_id}/pagos/{pago_id}`
- POST `/pedido-clientes/{pc_id}/pagos/{pago_id}/comprobante`

### Stats
- GET `/stats/dashboard` — metricas generales (pedidos, clientes, cobrado, pendiente)
- GET `/stats/clientes/{id}` — historial completo de un cliente con totales

## Variables de entorno requeridas
```
DATABASE_URL
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
```

## Correr localmente
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Documentacion en: http://localhost:8000/docs

## Convenciones
- Calculos financieros siempre con Decimal, nunca float
- Imagenes de productos → Cloudinary folder: facturador/productos
- Comprobantes de pago → Cloudinary folder: facturador/comprobantes
- Los errores usan HTTPException con codigos estandar
- La funcion _calcular_saldo() en stats.py y pedidos.py debe mantenerse consistente
