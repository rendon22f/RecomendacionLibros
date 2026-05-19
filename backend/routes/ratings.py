from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.recommendation_service import (
    guardar_calificacion
)

router = APIRouter()


class RatingData(BaseModel):

    id_usuario: int
    id_libro: int
    calificacion: int


@router.post("/ratings")
def post_rating(datos: RatingData):

    resultado = guardar_calificacion(

        datos.id_usuario,
        datos.id_libro,
        datos.calificacion
    )

    return resultado