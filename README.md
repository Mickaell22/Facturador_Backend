# 🛒 Facturador Temu — Backend

API REST para gestionar pedidos grupales de Temu. Registra clientes, artículos, pagos y genera resúmenes por pedido.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Cloudinary](https://img.shields.io/badge/Cloudinary-Imágenes-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-Deploy-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)

---

## Características

- Gestión de **clientes** con comisión configurable por cliente y aliases para normalizar nombres
- Gestión de **pedidos** con múltiples clientes por pedido
- Registro de **artículos** con link de Temu, precio, imagen e indicador de llegada
- Registro de **pagos** con foto del comprobante (transferencia, efectivo, etc.)
- Cálculo automático de subtotal, comisión, total pagado y saldo pendiente
- Subida de imágenes a **Cloudinary**
- Documentación interactiva en `/docs`

---

## Estructura del proyecto

```
backend/
├── main.py              # Entry point, CORS, rutas
├── database.py          # Conexión SQLAlchemy + sesión
├── models.py            # Modelos ORM
├── schemas.py           # Esquemas Pydantic
├── requirements.txt
├── Procfile             # Para Railway
├── routers/
│   ├── clientes.py
│   ├── pedidos.py
│   ├── items.py
│   └── pagos.py
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

La API estará disponible en `http://localhost:8000`
Documentación interactiva en `http://localhost:8000/docs`

---

## Deploy en Railway

1. Crea un nuevo proyecto en [Railway](https://railway.app)
2. Agrega un servicio **PostgreSQL**
3. Conecta este repositorio como un nuevo servicio
4. Agrega las variables de entorno en Railway (Settings → Variables)
5. Railway usa el `Procfile` para iniciar la app automáticamente

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/clientes` | Listar clientes |
| POST | `/clientes` | Crear cliente |
| GET | `/pedidos` | Listar pedidos |
| POST | `/pedidos` | Crear pedido |
| GET | `/pedidos/{id}` | Ver pedido con totales |
| POST | `/pedidos/{id}/clientes/{id}` | Agregar cliente a pedido |
| POST | `/pedido-clientes/{id}/items` | Agregar artículo |
| POST | `/pedido-clientes/{id}/pagos` | Registrar pago |
| POST | `/pedido-clientes/{id}/items/{id}/imagen` | Subir imagen de producto |
| POST | `/pedido-clientes/{id}/pagos/{id}/comprobante` | Subir comprobante de pago |

---

## Lógica de cálculo

```
subtotal        = suma de precios donde llegado = true
comisión        = cantidad de items llegados × comisión del cliente
total           = subtotal + comisión
total pagado    = suma de todos los pagos registrados
saldo pendiente = total − total pagado
```
