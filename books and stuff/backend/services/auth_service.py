from backend.database.connection import conectar


def ejecutar_login(username, password):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT id_usuario, username, tipo, primer_ingreso
        FROM usuarios
        WHERE username = %s
        AND contrasena = %s
    """

    cursor.execute(sql, (username, password))

    resultado = cursor.fetchone()

    db.close()

    return resultado