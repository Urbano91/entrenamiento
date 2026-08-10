# Plataforma de Entrenamiento de Fútbol (Fase 1)

## Objetivo
Aplicación web profesional para gestionar una plataforma de entrenamiento de fútbol, partiendo de una extensa validada base de datos SQLite preexistente. Permite a usuarios autenticados explorar, buscar y ver detalles de más de cien ejercicios con imágenes, tiempos, espacios, objetivos y número de jugadores asociados.

## Stack Tecnológico
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy, Pydantic, Passlib, PyJWT y pytest. Base de Datos local montada con SQLite.
- **Frontend:** Node.js 18+, React, Vite, TypeScript, TailwindCSS, React Router y Lucide Icons.

## Arquitectura
La plataforma sigue un diseño limpio y moderno dividida en dos contenedores principales:
- **Backend (FastAPI Model-View-Controller)** protegiendo los datos con Auth por Cookies HttpOnly. La fuente de la verdad para datos reposa enteramente sobre SQLite, garantizando fidelidad.
- **Frontend (React)** se conecta únicamente a través de REST APIs seguras. El listado renderiza tarjetas concisas, y se usa paginación dinámica del lado del servidor.

## Estructura
```text
futbol-db/
├── backend/
│   ├── app/ (Lógica API)
│   ├── tests/ (Pruebas Automatizadas)
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/ (React código fuente)
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── database/
│   ├── futbol_entrenamiento.sqlite
│   └── imagenes/
└── README.md
```

## Requisitos
- Python 3.10+
- Node.js 18+

## Configuración e Instalación

### Base de Datos
La base de datos original reposa en `database/futbol_entrenamiento.sqlite`. Asegúrate de no mover esta carpeta o actualizar la variable `DATABASE_URL` correctamente.

### Backend
1. Navegar a `backend/`
2. Crear un entorno virtual `python3 -m venv venv`
3. Activar el entorno `source venv/bin/activate`
4. Instalar dependencias mediante `pip install -r requirements.txt`
5. Configurar el archivo `.env` basándose en `.env.example`

### Creación de Usuarios (Admin)
No hay autorregistro de momento por diseño. Únicamente el sistema crea mediante script. 
Aún posicionándote sobre el `backend/` dentro del entorno virtual, ejecuta:
```bash
python3 -m app.scripts.create_user
```
Inserta tu `Usuario` y `Contraseña` y presiona enter.

### Ejecutar Servidor Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.1 --port 8000
```
La documentación interactiva será montada en: `http://localhost:8000/docs`

### Frontend
1. Navega a `frontend/`
2. Instala los módulos con `npm install`
3. Ejecuta el servidor dev: `npm run dev`
La app estará disponible por defecto en el puerto `5173`.

## Ejecución de Pruebas
Existen tests E2E y de Unidades programados.
Para ejecutarlos, ingresa a `backend/`, activa el entorno y corre en la terminal:
```bash
PYTHONPATH=. pytest tests/
```

## API Endpoints List (Principales)
- `POST /api/auth/login`: Autenticación con cookie JWT.
- `POST /api/auth/logout`: Eliminar la sesión local.
- `GET /api/ejercicios`: Obtenención paginada con text search, `page`, `page_size`, y filtros dinámicos.
- `GET /api/ejercicios/{id}`: Detalle expansivo.
- `GET /api/imagenes/{id}`: Proxy de acceso controlado de multimedia para protección de rutas externas.

## Validación de Datos
La SQLite proporcionada contiene las validaciones originales confirmando:
- 114 ejercicios
- 10 tipos de tareas
- ~980 textos y múltiples relaciones con imágenes.
Los tests de la API garantizan un mínimo de resiliencia y ninguna consulta rompe las reglas establecidas. Nada fue alterado ni borrado (manteniendo la SQLite como fuente inmutable).
