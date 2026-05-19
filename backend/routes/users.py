from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.recommendation_service import finalizar_primer_ingreso
from backend.database.connection import conectar

router = APIRouter()



class UserData(BaseModel):
    id_usuario: int


@router.put("/finish-onboarding")
def finish_onboarding(datos: UserData):
    resultado = finalizar_primer_ingreso(datos.id_usuario)
    return resultado



class UsuarioBase(BaseModel):
    username: str
    contrasena: str
    tipo: int


@router.get("/api/users")
def obtener_usuarios():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id_usuario, username, tipo, primer_ingreso FROM usuarios")
    usuarios = cursor.fetchall()
    db.close()
    return usuarios



@router.post("/api/users")
def crear_usuario(usuario: UsuarioBase):
    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios WHERE username = %s", (usuario.username,))
    if cursor.fetchone():
        db.close()
        raise HTTPException(status_code=400, detail="Error: Ese nombre de usuario ya existe.")

    sql = "INSERT INTO usuarios (username, contrasena, tipo, primer_ingreso) VALUES (%s, %s, %s, 1)"
    cursor.execute(sql, (usuario.username, usuario.contrasena, usuario.tipo))
    db.commit()
    db.close()
    return {"success": True, "message": f"Usuario '{usuario.username}' creado con éxito"}


from typing import Optional


class UserUpdate(BaseModel):
    username: Optional[str] = None
    contrasena: Optional[str] = None
    tipo: Optional[int] = None


@router.put("/api/users/{id_usuario}")
def modificar_usuario(id_usuario: int, usuario: UserUpdate):
    db = conectar()
    cursor = db.cursor(dictionary=True)


    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    u_actual = cursor.fetchone()
    if not u_actual:
        db.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")


    nuevo_nom = usuario.username if usuario.username else u_actual['username']
    nueva_pass = usuario.contrasena if usuario.contrasena else u_actual['contrasena']
    nuevo_tipo = usuario.tipo if usuario.tipo is not None else u_actual['tipo']


    sql = "UPDATE usuarios SET username = %s, contrasena = %s, tipo = %s WHERE id_usuario = %s"
    cursor.execute(sql, (nuevo_nom, nueva_pass, nuevo_tipo, id_usuario))
    db.commit()
    db.close()
    return {"success": True, "message": "Datos actualizados correctamente."}


@router.delete("/api/users/{id_usuario}")
def eliminar_usuario(id_usuario: int):
    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    db.commit()
    db.close()
    return {"success": True, "message": "Usuario eliminado correctamente."}