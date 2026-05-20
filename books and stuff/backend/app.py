print("ESTOY ENTRANDO AL APP CORRECTO")
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


from backend.services.auth_service import ejecutar_login
from backend.services.book_service import obtener_libros
from backend.services.stats_service import obtener_estadisticas_plataforma


from backend.routes.books import router as books_router


app = FastAPI(
    title="Sistema de Recomendación de Libros Analytics"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(books_router)


class LoginRequest(BaseModel):
    username: str
    password: str



@app.post("/auth/login")
def login(credentials: LoginRequest):
    """
    Ruta encargada de procesar la autenticación
    """

    resultado = ejecutar_login(
        credentials.username,
        credentials.password
    )

    # Validación de credenciales
    if not resultado:
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos"
        )

    # Respuesta estructurada
    return {
        "id_usuario": resultado["id_usuario"],
        "username": resultado["username"],
        "tipo": resultado["tipo"],
        "primer_ingreso": resultado["primer_ingreso"]
    }



@app.get("/books")
def get_books():
    """
    Consulta del catálogo de libros
    """
    return obtener_libros()


@app.get("/books/stats")
def get_stats():
    """
    Consumo de métricas analíticas
    """

    resultados = obtener_estadisticas_plataforma()

    if "error" in resultados:
        raise HTTPException(
            status_code=500,
            detail=resultados["error"]
        )

    return resultados



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )