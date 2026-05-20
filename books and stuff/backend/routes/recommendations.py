from fastapi import APIRouter

from backend.services.recommendation_service import (
    obtener_generos,
    obtener_libros_genero,
    mostrar_recomendaciones
)

router = APIRouter()


@router.get("/genres")
def get_generos():

    generos = obtener_generos()

    return {
        "generos": generos
    }


@router.get("/onboarding/books/{genero}")
def get_books_by_genre(genero: str):

    libros = obtener_libros_genero(genero)

    return {
        "libros": libros
    }


@router.get("/recommendations/{id_usuario}")
def get_recommendations(id_usuario: int):

    libros = mostrar_recomendaciones(id_usuario)

    return {
        "recommendations": libros
    }