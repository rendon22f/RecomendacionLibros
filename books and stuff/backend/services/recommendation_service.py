from backend.database.connection import conectar

def obtener_generos():

    db = conectar()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT genero FROM libros"
    )

    generos = cursor.fetchall()

    db.close()

    return generos


def obtener_libros_genero(genero):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT id_libro, titulo, autor
        FROM libros
        WHERE genero = %s
        ORDER BY RAND()
        LIMIT 5
    """

    cursor.execute(query, (genero,))

    libros = cursor.fetchall()

    db.close()

    return libros


def guardar_calificacion(
    id_usuario,
    id_libro,
    calificacion
):

    db = conectar()
    cursor = db.cursor()

    query = """
        INSERT INTO puntuacion
        (id_usuario, id_libro, calificacion)
        VALUES (%s, %s, %s)
    """

    cursor.execute(
        query,
        (id_usuario, id_libro, calificacion)
    )

    db.commit()
    db.close()

    return {
        "success": True
    }


def finalizar_primer_ingreso(id_usuario):

    db = conectar()
    cursor = db.cursor()

    query = """
        UPDATE usuarios
        SET primer_ingreso = 0
        WHERE id_usuario = %s
    """

    cursor.execute(query, (id_usuario,))

    db.commit()
    db.close()

    return {
        "success": True
    }



def mostrar_recomendaciones(id_usuario):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql_generos = """
        SELECT l.genero, AVG(p.calificacion) as promedio
        FROM puntuacion p
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.id_usuario = %s
        GROUP BY l.genero
        ORDER BY promedio DESC, COUNT(*) DESC
        LIMIT 2
    """

    cursor.execute(sql_generos, (id_usuario,))
    mejores_generos = cursor.fetchall()

    libros_finales = []

    if mejores_generos:

        gen_1 = mejores_generos[0]['genero']

        cursor.execute("""
            SELECT id_libro, titulo, autor, genero
            FROM libros
            WHERE genero = %s
            AND id_libro NOT IN (
                SELECT id_libro
                FROM puntuacion
                WHERE id_usuario = %s
            )
            ORDER BY RAND()
            LIMIT 3
        """, (gen_1, id_usuario))

        libros_finales.extend(cursor.fetchall())

        if len(mejores_generos) > 1:

            gen_2 = mejores_generos[1]['genero']

            cursor.execute("""
                SELECT id_libro, titulo, autor, genero
                FROM libros
                WHERE genero = %s
                AND id_libro NOT IN (
                    SELECT id_libro
                    FROM puntuacion
                    WHERE id_usuario = %s
                )
                ORDER BY RAND()
                LIMIT 1
            """, (gen_2, id_usuario))

            libros_finales.extend(cursor.fetchall())

        cursor.execute("""
            SELECT id_libro, titulo, autor, genero
            FROM libros
            WHERE genero != %s
            AND id_libro NOT IN (
                SELECT id_libro
                FROM puntuacion
                WHERE id_usuario = %s
            )
            ORDER BY RAND()
            LIMIT 1
        """, (gen_1, id_usuario))

        libros_finales.extend(cursor.fetchall())

    if len(libros_finales) < 5:

        faltantes = 5 - len(libros_finales)

        ids_ya_incluidos = [l['id_libro'] for l in libros_finales]

        if not ids_ya_incluidos:
            ids_ya_incluidos = [0]

        ids_str = ",".join(map(str, ids_ya_incluidos))

        query_fill = f"""
            SELECT id_libro, titulo, autor, genero
            FROM libros
            WHERE id_libro NOT IN ({ids_str})
            AND id_libro NOT IN (
                SELECT id_libro
                FROM puntuacion
                WHERE id_usuario = %s
            )
            ORDER BY RAND()
            LIMIT {faltantes}
        """

        cursor.execute(query_fill, (id_usuario,))
        libros_finales.extend(cursor.fetchall())

    db.close()

    return libros_finales
