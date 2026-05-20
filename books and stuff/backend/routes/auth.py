from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.auth_service import ejecutar_login

router = APIRouter()


class LoginData(BaseModel):

    username: str
    password: str


@router.post("/login")
def login(datos: LoginData):

    usuario = ejecutar_login(
        datos.username,
        datos.password
    )

    if usuario:

        return {
            "success": True,
            "usuario": usuario
        }

    return {
        "success": False,
        "mensaje": "Credenciales incorrectas"
    }