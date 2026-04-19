# Backend — FastAPI

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Railway)
- Cloudinary (imagenes)
- Alembic (migraciones de BD)
- python-jose (JWT)
- httpx (Google OAuth)

## Estructura
```
backend/
├── main.py              # app FastAPI, CORS, registro de routers
├── database.py          # engine, SessionLocal, Base, get_db
├── models.py            # modelos ORM (tablas)
├── schemas.py           # esquemas Pydantic (request/response)
├── Procfile             # comando de inicio para Railway
├── requirements.txt
├── alembic.ini          # configuracion de migraciones
├── alembic/
│   ├── env.py           # usa DATABASE_URL del .env, importa Base y models
│   └── versions/        # archivos de migracion generados
├── .env                 # credenciales locales (no se sube)
├── .env.example         # plantilla sin valores reales
├── routers/
│   ├── auth.py          # Google OAuth + JWT + get_current_user dependency
│   ├── clientes.py      # CRUD clientes + aliases (delete protegido si tiene pedidos)
│   ├── pedidos.py       # CRUD pedidos + agregar/quitar clientes
│   ├── items.py         # CRUD items + subida de imagen
│   ├── pagos.py         # CRUD pagos + subida de comprobante
│   ├── stats.py         # estadisticas dashboard + historial por cliente
│   └── publico.py       # factura publica por token (sin auth)
└── utils/
    └── cloudinary_helper.py  # upload_image(), delete_image()
```

## Endpoints disponibles

### Auth (sin JWT requerido)
- GET `/auth/google/login` — redirige a Google OAuth
- GET `/auth/google/callback` — recibe code, valida email, emite JWT, redirige al frontend

### Clientes (requieren JWT)
- GET/POST `/clientes`
- GET/PUT/DELETE `/clientes/{id}` — DELETE bloqueado si tiene pedidos
- POST `/clientes/{id}/aliases`
- DELETE `/clientes/{id}/aliases/{alias_id}`

### Pedidos (requieren JWT)
- GET/POST `/pedidos`
- GET/PUT/DELETE `/pedidos/{id}`
- POST/DELETE `/pedidos/{id}/clientes/{cliente_id}`

### Items (requieren JWT)
- GET/POST `/pedido-clientes/{pc_id}/items`
- PUT/DELETE `/pedido-clientes/{pc_id}/items/{item_id}`
- POST `/pedido-clientes/{pc_id}/items/{item_id}/imagen`

### Pagos (requieren JWT)
- GET/POST `/pedido-clientes/{pc_id}/pagos`
- DELETE `/pedido-clientes/{pc_id}/pagos/{pago_id}`
- POST `/pedido-clientes/{pc_id}/pagos/{pago_id}/comprobante`

### Stats (requieren JWT)
- GET `/stats/dashboard` — metricas generales
- GET `/stats/clientes/{id}` — historial completo de un cliente

### Publico (sin JWT)
- GET `/public/factura/{token}` — datos de factura por token_publico

## Variables de entorno requeridas
```
DATABASE_URL
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI        # http://localhost:8000/auth/google/callback (dev)
JWT_SECRET                 # string largo y aleatorio
ALLOWED_EMAIL              # unico correo autorizado
FRONTEND_URL               # http://localhost:5173 (dev)
```

## Optimizaciones de rendimiento aplicadas
- Connection pool configurado en `database.py`: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=1800`
- CORS restringido a `FRONTEND_URL` en lugar de `"*"`
- Uvicorn corre con `--workers 2` para manejar requests concurrentes
- `alembic upgrade head` removido del Procfile — debe configurarse como **Deploy Command** en Railway dashboard (solo corre en nuevos deploys, no en cold starts)

## Deploy en Railway (serverless)
- **Deploy Command** (Railway dashboard): `alembic upgrade head`
- **Start Command** (Procfile): `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2`
- Recursos: ~512MB RAM, 0.5 vCPU compartida (plan Hobby)
- Para Always On: cambiar a plan Pro (~$5/mes por servicio)

## Correr localmente
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```
Documentacion en: http://localhost:8000/docs

## Migraciones con Alembic
```bash
# Ver estado actual
alembic current

# Generar migracion automatica al cambiar models.py
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones pendientes
alembic upgrade head
```

En Railway el Procfile corre `alembic upgrade head` antes de iniciar uvicorn, por lo que las migraciones se aplican automaticamente en cada deploy. El `create_all` fue eliminado de main.py — Alembic es la unica fuente de verdad del schema.

## Soft delete
- Las tablas clientes, pedidos, pedido_clientes, items y pagos tienen columna `deleted_at TIMESTAMP`
- Los endpoints DELETE hacen `deleted_at = now()` en lugar de borrar fisicamente
- Eliminar pedido o quitar cliente del pedido hace cascade suave sobre sus items y pagos
- Todos los listados filtran `WHERE deleted_at IS NULL`
- Los calculos de totales filtran en Python: `[i for i in pc.items if i.deleted_at is None]`

## Convenciones
- Calculos financieros siempre con Decimal, nunca float
- Queries con colecciones usan selectinload (evita producto cartesiano de joinedload)
- Imagenes de productos → Cloudinary folder: facturador/productos
- Comprobantes de pago → Cloudinary folder: facturador/comprobantes
- Los errores usan HTTPException con codigos estandar
- calcular_totales() en pedidos.py y _calcular_saldo() en stats.py deben mantenerse consistentes
- El router publico.py NO usa la dependency get_current_user
