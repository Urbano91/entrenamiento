from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    admin, auth, calendario, catalogos, club, ejercicios, entrenamientos, imagenes, partidos,
    perfil, planificaciones, taxonomia, temporadas, training_load,
)

app = FastAPI(title="Base de Entrenamiento de Fútbol API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://futbol-db-xz04.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Fase 1
app.include_router(auth.router)
app.include_router(ejercicios.router)
app.include_router(catalogos.router)
app.include_router(imagenes.router)
app.include_router(taxonomia.router)
app.include_router(club.router)
app.include_router(admin.router)

# Fase 2
app.include_router(perfil.router)
app.include_router(temporadas.router)
app.include_router(entrenamientos.router)
app.include_router(calendario.router)
app.include_router(partidos.router)
app.include_router(planificaciones.router)
app.include_router(planificaciones.documents_router)
app.include_router(training_load.router)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "3.1.0"}
