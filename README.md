# Facturador Temu — Backend

API REST para gestionar pedidos grupales de Temu. Registra clientes, artículos, pagos y genera resúmenes financieros por pedido.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Cloudinary](https://img.shields.io/badge/Cloudinary-Imágenes-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-Deploy-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)

---

## Características

- Gestión de **clientes** con comisión configurable y aliases para normalizar nombres
- Gestión de **pedidos** con múltiples clientes por pedido
- Registro de **artículos** con link de Temu, precio, imagen e indicador de llegada
- Registro de **pagos** con foto del comprobante (transferencia / efectivo)
- Cálculo automático de subtotal, comisión, total pagado y saldo pendiente
- **Exportación a Excel** (multi-hoja por pedido)
- **Dashboard de estadísticas** globales
- **Rutas públicas** por token: historial del cliente y factura sin login
- Autenticación con **Google OAuth** + JWT
- Subida de imágenes a **Cloudinary**
- Documentación interactiva en `/docs`

---

## Estructura del proyecto

```
backend/
├── main.py                  # Entry point, CORS, routers
├── database.py              # Conexión SQLAlchemy + sesión
├── models.py                # Modelos ORM (soft delete)
├── schemas.py               # Esquemas Pydantic
├── requirements.txt
├── Procfile                 # Para Railway
├── routers/
│   ├── auth.py              # Google OAuth + JWT
│   ├── clientes.py
│   ├── pedidos.py
│   ├── items.py
│   ├── pagos.py
│   ├── stats.py             # Dashboard de estadísticas
│   ├── export.py            # Exportación a Excel
│   └── publico.py           # Rutas públicas por token
└── utils/
    └── cloudinary_helper.py
```

---

## Variables de entorno

Crea un archivo `.env` basado en `.env.example`:

```env
DATABASE_URL=postgresql://usuario:password@host:5432/facturador

CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

# Google OAuth (console.cloud.google.com)
GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# JWT — genera con: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=genera-un-string-largo-y-aleatorio-aqui

# Solo este email puede iniciar sesión
ALLOWED_EMAIL=tu_email@gmail.com

FRONTEND_URL=http://localhost:5173
```

---

## Instalación local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Correr servidor
uvicorn main:app --reload
```

API disponible en `http://localhost:8000`
Documentación interactiva en `http://localhost:8000/docs`

---

## Endpoints principales

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/auth/google/login` | — | Inicia OAuth con Google |
| GET | `/auth/google/callback` | — | Callback OAuth, devuelve JWT |
| GET | `/clientes` | JWT | Listar clientes |
| POST | `/clientes` | JWT | Crear cliente |
| GET | `/pedidos` | JWT | Listar pedidos |
| POST | `/pedidos` | JWT | Crear pedido |
| GET | `/pedidos/{id}` | JWT | Ver pedido con totales |
| POST | `/pedidos/{id}/clientes/{id}` | JWT | Agregar cliente a pedido |
| POST | `/pedido-clientes/{id}/items` | JWT | Agregar artículo |
| POST | `/pedido-clientes/{id}/pagos` | JWT | Registrar pago |
| POST | `/pedido-clientes/{id}/items/{id}/imagen` | JWT | Subir imagen de producto |
| POST | `/pedido-clientes/{id}/pagos/{id}/comprobante` | JWT | Subir comprobante |
| GET | `/pedidos/{id}/export` | JWT | Exportar a Excel |
| GET | `/stats/dashboard` | JWT | Estadísticas globales |
| GET | `/public/factura/{token}` | — | Factura pública del cliente |
| GET | `/public/cliente/{token}` | — | Historial público del cliente |

---

## Lógica de cálculo

```
subtotal        = suma de precios donde llegado = true
comisión        = cantidad de items llegados × comisión del cliente
total           = subtotal + comisión
total pagado    = suma de todos los pagos registrados
saldo pendiente = total − total pagado
```

---

## Deploy en Railway

1. Crea un nuevo proyecto en [Railway](https://railway.app)
2. Agrega un servicio **PostgreSQL**
3. Conecta este repositorio como un nuevo servicio
4. Agrega las variables de entorno en Railway (Settings → Variables)
5. Railway usa el `Procfile` para iniciar la app automáticamente
