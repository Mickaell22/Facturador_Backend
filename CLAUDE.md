# Backend — FastAPI

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Railway)
- Cloudinary (imágenes)
- Alembic (migraciones, futuro)

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
│   └── pagos.py         # CRUD pagos + subida de comprobante
└── utils/
    └── cloudinary_helper.py  # upload_image(), delete_image()
```

## Variables de entorno requeridas
```
DATABASE_URL              # conexión PostgreSQL
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
```

## Correr localmente
```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
Documentación en: http://localhost:8000/docs

## Convenciones
- Cada router usa su propio prefijo y tag
- Los cálculos financieros se hacen con Decimal, nunca float
- Las imágenes se suben a Cloudinary en carpetas separadas:
  - productos  → facturador/productos
  - comprobantes → facturador/comprobantes
- Los errores usan HTTPException con códigos estándar
