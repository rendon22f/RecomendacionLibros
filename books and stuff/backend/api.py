from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from backend.services.auth_service import ejecutar_login
from backend.services.book_service import obtener_libros
from backend.services.stats_service import obtener_estadisticas_plataforma
from backend.database.connection import conectar


from backend.routes.books import router as books_router


app = FastAPI(title="Sistema de Recomendación de Libros - API Unificada")


app.include_router(books_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class LoginRequest(BaseModel):
    username: str
    password: str


class UserSchema(BaseModel):
    username: str
    contrasena: str
    tipo: int


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    contrasena: Optional[str] = None
    tipo: Optional[int] = None


class RatingSchema(BaseModel):
    id_usuario: int
    id_libro: int
    calificacion: int


class OnboardingSchema(BaseModel):
    id_usuario: int


@app.post("/auth/login")
def login(credentials: LoginRequest):

    resultado = ejecutar_login(
        credentials.username,
        credentials.password
    )

    if not resultado:
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos"
        )

    return {
        "id_usuario": resultado["id_usuario"],
        "username": resultado["username"],
        "tipo": resultado["tipo"],
        "primer_ingreso": resultado["primer_ingreso"]
    }


@app.get("/api/users")
def api_obtener_usuarios():

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_usuario, username, tipo, primer_ingreso
        FROM usuarios
    """)

    usuarios = cursor.fetchall()

    db.close()

    return usuarios


@app.post("/api/users")
def api_crear_usuario(user: UserSchema):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM usuarios WHERE username = %s",
        (user.username,)
    )

    if cursor.fetchone():

        db.close()

        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario ya existe."
        )

    sql = """
        INSERT INTO usuarios
        (username, contrasena, tipo, primer_ingreso)
        VALUES (%s, %s, %s, 1)
    """

    cursor.execute(
        sql,
        (user.username, user.contrasena, user.tipo)
    )

    db.commit()
    db.close()

    return {
        "message": "Usuario creado con éxito."
    }


@app.put("/api/users/{id_usuario}")
def api_modificar_usuario(
        id_usuario: int,
        user: UserUpdateSchema
):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM usuarios WHERE id_usuario = %s",
        (id_usuario,)
    )

    usuario_actual = cursor.fetchone()

    if not usuario_actual:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado."
        )

    nuevo_nom = (
        user.username
        if user.username
        else usuario_actual['username']
    )

    nueva_pass = (
        user.contrasena
        if user.contrasena
        else usuario_actual['contrasena']
    )

    nuevo_tipo = (
        user.tipo
        if user.tipo is not None
        else usuario_actual['tipo']
    )

    sql = """
        UPDATE usuarios
        SET username = %s,
            contrasena = %s,
            tipo = %s
        WHERE id_usuario = %s
    """

    cursor.execute(
        sql,
        (nuevo_nom, nueva_pass, nuevo_tipo, id_usuario)
    )

    db.commit()
    db.close()

    return {
        "message": "Registro actualizado correctamente."
    }


@app.delete("/api/users/{id_usuario}")
def api_eliminar_usuario(id_usuario: int):

    db = conectar()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM usuarios WHERE id_usuario = %s",
        (id_usuario,)
    )

    db.commit()
    db.close()

    return {
        "message": "Usuario eliminado correctamente."
    }


# =========================================================
#  3. CONFIGURACIÓN DE GUSTOS Y RECOMENDACIONES
# =========================================================
@app.get("/genres")
def obtener_generos():

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT genero FROM libros"
    )

    generos = cursor.fetchall()

    db.close()

    return {
        "generos": generos
    }


@app.get("/onboarding/books/{genero}")
def libros_onboarding(genero: str):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id_libro, titulo, autor, genero
        FROM libros
        WHERE genero = %s
        LIMIT 10
        """,
        (genero,)
    )

    libros = cursor.fetchall()

    db.close()

    return {
        "libros": libros
    }


@app.post("/ratings")
def guardar_calificacion(rating: RatingSchema):

    db = conectar()
    cursor = db.cursor()

    sql = """
        INSERT INTO puntuacion
        (id_usuario, id_libro, calificacion)
        VALUES (%s, %s, %s)

        ON DUPLICATE KEY UPDATE
        calificacion = VALUES(calificacion)
    """

    cursor.execute(
        sql,
        (
            rating.id_usuario,
            rating.id_libro,
            rating.calificacion
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Calificación guardada"
    }


@app.put("/finish-onboarding")
def finalizar_onboarding(data: OnboardingSchema):

    db = conectar()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE usuarios
        SET primer_ingreso = 0
        WHERE id_usuario = %s
        """,
        (data.id_usuario,)
    )

    db.commit()
    db.close()

    return {
        "message": "Perfil configurado"
    }


@app.get("/recommendations/{id_usuario}")
def obtener_recomendaciones_usuario(id_usuario: int):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_libro, titulo, autor, genero
        FROM libros
        ORDER BY RAND()
        LIMIT 6
    """)

    libros = cursor.fetchall()

    db.close()

    return {
        "recommendations": libros
    }



@app.get("/books/stats")
def get_stats():

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
        "backend.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )