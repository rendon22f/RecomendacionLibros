from fastapi import APIRouter, HTTPException

from backend.services.book_service import (
    obtener_libros,
    importar_desde_api
)

from backend.services.stats_service import (
    obtener_estadisticas_plataforma
)

router = APIRouter()


@router.get("/books")
def get_books():

    return obtener_libros()



@router.post("/books/sync")
def sync_books():

    try:

        importar_desde_api()

        return {
            "success": True,
            "message": "¡Sincronización completada!"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



@router.get("/books/stats")
def get_stats():

    resultados = obtener_estadisticas_plataforma()

    if "error" in resultados:

        raise HTTPException(
            status_code=500,
            detail=resultados["error"]
        )

    return resultados

@router.get("/test")
def test_route():

    return {
        "message": "Ruta funcionando correctamente"
    }