

import mysql.connector
import requests
import random


# CONEXIÓN CENTRALIZADA
def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="recomendacion",
        charset="utf8"
    )


# ALIMENTACIÓN DE LA BASE (SÓLO ADMIN)
def importar_desde_api():
    temas = ["fiction", "horror", "sci-fi", "history", "fantasy", "mystery", "thriller", "science", "biography"]
    tema_azar = random.choice(temas)
    pagina_azar = random.randint(1, 100)

    print(f"\n [API] Trayendo libros de '{tema_azar}' (Página {pagina_azar})...")
    url = f"https://openlibrary.org/search.json?q={tema_azar}&limit=10&page={pagina_azar}"

    try:
        res = requests.get(url).json()
        db = conectar()
        cursor = db.cursor()

        libros_nuevos = 0

        for doc in res.get('docs', []):
            titulo = doc.get('title', 'Sin título')[:100]
            autor = doc.get('author_name', ['Anónimo'])[0][:50]
            anio = doc.get('first_publish_year', 0)

            generos_api = doc.get('subject', [])
            genero = "General"

            for g in generos_api:
                if g.lower() not in ["fiction", "general", "accessible book", "protected daisy"]:
                    genero = g.capitalize()
                    break

            if genero == "General":
                genero = tema_azar.capitalize()

            query = """
                INSERT IGNORE INTO libros
                (titulo, genero, autor, anio)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(query, (titulo, genero, autor, anio))

            if cursor.rowcount > 0:
                libros_nuevos += 1

        db.commit()
        db.close()

        print(f" ¡Éxito! Se agregaron {libros_nuevos} libros nuevos.")

    except Exception as e:
        print(f" Error en la API: {e}")


#  MOSTRAR RECOMENDACIONES
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

    print("\n" + "=" * 50)
    print("   TUS RECOMENDACIONES PERSONALIZADAS ")
    print("=" * 50)

    if not libros_finales:
        print(" ¡Vaya! No encontramos libros nuevos para recomendarte.")

    else:

        for i, l in enumerate(libros_finales, 1):

            if mejores_generos and i <= 3 and l['genero'] == mejores_generos[0]['genero']:
                tag = " [Recomendado]"
            elif i == 5:
                tag = " [Nuevo]"
            else:
                tag = " [Podría gustarte]"

            print(f"{i}. {tag} {l['titulo']} - {l['autor']} | {l['genero']} (ID: {l['id_libro']})")

    print("\n" + "-" * 50)

    opcion = input("¿Quieres calificar alguno de estos libros ahora? (s/n): ")

    if opcion.lower() == 's':

        try:
            num = int(input("Ingresa el número de la lista (1-5): "))

            if 1 <= num <= len(libros_finales):

                libro_sel = libros_finales[num - 1]

                calif = int(input(
                    f"¿Qué calificación le das a '{libro_sel['titulo']}'? (1-5): "
                ))

                if 1 <= calif <= 5:

                    sql_ins = """
                        INSERT INTO puntuacion
                        (id_usuario, id_libro, calificacion)
                        VALUES (%s, %s, %s)
                    """

                    cursor.execute(
                        sql_ins,
                        (id_usuario, libro_sel['id_libro'], calif)
                    )

                    db.commit()

                    print(
                        f"¡Guardado! Tu opinión sobre '{libro_sel['titulo']}' nos ayuda a mejorar."
                    )

                else:
                    print("Debe ser entre 1 y 5.")

            else:
                print("Selección fuera de rango.")

        except ValueError:
            print("Por favor, usa números.")

    db.close()


def ejecutar_login():

    db = conectar()
    cursor = db.cursor()

    print("\n" + "=" * 30 + "\n   SISTEMA DE LIBROS    \n" + "=" * 30)

    user = input("Usuario (o 'exit'): ")

    if user.lower() == 'exit':
        return "EXIT"

    psw = input("Contraseña: ")

    sql = """
        SELECT id_usuario, username, tipo, primer_ingreso
        FROM usuarios
        WHERE username = %s
        AND contrasena = %s
    """

    cursor.execute(sql, (user, psw))

    resultado = cursor.fetchone()

    db.close()

    return resultado


def gestionar_usuarios():

    while True:

        db = conectar()
        cursor = db.cursor(dictionary=True)

        print("\n" + "-" * 25)
        print("   GESTIÓN DE USUARIOS")
        print("-" * 25)

        print("1. Ver todos los usuarios")
        print("2. Crear nuevo usuario")
        print("3. MODIFICAR usuario")
        print("4. Eliminar usuario")
        print("5. Volver al menú anterior")

        opcion = input("\nSelecciona una opción: ")

        if opcion == '1':

            cursor.execute(
                "SELECT id_usuario, username, tipo, primer_ingreso FROM usuarios"
            )

            usuarios = cursor.fetchall()

            print("\nID | Usuario | Tipo | ¿Es nuevo?")

            for u in usuarios:

                tipo_txt = "Admin" if u['tipo'] == 1 else "User"
                nuevo_txt = "Sí" if u['primer_ingreso'] == 1 else "No"

                print(f"{u['id_usuario']} | {u['username']} | {tipo_txt} | {nuevo_txt}")

        elif opcion == '2':

            nuevo_nom = input("Nombre de usuario: ")
            nuevo_pass = input("Contraseña: ")
            nuevo_tipo = input("Tipo (1 para Admin, 2 para User): ")

            cursor.execute(
                "SELECT * FROM usuarios WHERE username = %s",
                (nuevo_nom,)
            )

            if cursor.fetchone():
                print("Error: Ese nombre de usuario ya existe.")

            else:

                sql = """
                    INSERT INTO usuarios
                    (username, contrasena, tipo, primer_ingreso)
                    VALUES (%s, %s, %s, 1)
                """

                cursor.execute(sql, (nuevo_nom, nuevo_pass, nuevo_tipo))

                db.commit()

                print(f"Usuario '{nuevo_nom}' creado con éxito.")

        elif opcion == '3':

            id_mod = input("Ingresa el ID del usuario que quieres MODIFICAR: ")

            cursor.execute(
                "SELECT * FROM usuarios WHERE id_usuario = %s",
                (id_mod,)
            )

            usuario = cursor.fetchone()

            if usuario:

                print(f"\nModificando a: {usuario['username']}")
                print("(Deja en blanco para no cambiar el valor actual)")

                nuevo_nom = input(f"Nuevo nombre [{usuario['username']}]: ") or usuario['username']
                nuevo_pass = input("Nueva contraseña: ") or usuario['contrasena']
                nuevo_tipo = input(
                    f"Nuevo tipo (1:Admin, 2:User) [{usuario['tipo']}]: "
                ) or usuario['tipo']

                sql_update = """
                    UPDATE usuarios
                    SET username = %s,
                        contrasena = %s,
                        tipo = %s
                    WHERE id_usuario = %s
                """

                cursor.execute(
                    sql_update,
                    (nuevo_nom, nuevo_pass, nuevo_tipo, id_mod)
                )

                db.commit()

                print("Datos actualizados correctamente.")

            else:
                print("No se encontró un usuario con ese ID.")

        elif opcion == '4':

            id_borrar = input("Ingresa el ID del usuario a eliminar: ")

            confirmar = input(
                f"¿Estás seguro de eliminar al usuario ID {id_borrar}? (s/n): "
            )

            if confirmar.lower() == 's':

                cursor.execute(
                    "DELETE FROM usuarios WHERE id_usuario = %s",
                    (id_borrar,)
                )

                db.commit()

                print("Usuario eliminado.")

        elif opcion == '5':
            db.close()
            break

        db.close()



def alimentar_motor_usuario(id_usuario):

    db = conectar()
    cursor = db.cursor(dictionary=True)

    print("\n--- ¡VAMOS A CONFIGURAR TU PERFIL! ---")

    cursor.execute("SELECT DISTINCT genero FROM libros")

    generos = [row['genero'] for row in cursor.fetchall()]

    print("\nGéneros disponibles:")

    for i, g in enumerate(generos, 1):
        print(f"{i}. {g}")

    try:
        seleccion = int(input("\nSelecciona el número de tu género favorito: "))
        genero_elegido = generos[seleccion - 1]

    except (ValueError, IndexError):
        genero_elegido = "General"

    print(f"\nMostrando libros de {genero_elegido}:")

    cursor.execute(
        "SELECT id_libro, titulo, autor FROM libros WHERE genero = %s ORDER BY RAND() LIMIT 5",
        (genero_elegido,)
    )

    libros_a_calificar = cursor.fetchall()

    if not libros_a_calificar:
        print("No hay libros suficientes.")
        return

    for libro in libros_a_calificar:

        while True:

            try:
                calif = int(input(
                    f"¿Qué puntuación le das a '{libro['titulo']}'? (1-5): "
                ))

                if 1 <= calif <= 5:

                    cursor.execute(
                        "INSERT INTO puntuacion (id_usuario, id_libro, calificacion) VALUES (%s, %s, %s)",
                        (id_usuario, libro['id_libro'], calif)
                    )

                    break

                else:
                    print("Del 1 al 5.")

            except ValueError:
                print("Número inválido.")

    cursor.execute(
        "UPDATE usuarios SET primer_ingreso = 0 WHERE id_usuario = %s",
        (id_usuario,)
    )

    db.commit()
    db.close()

    print("\n¡Perfil configurado!")



if __name__ == "__main__":

    while True:

        datos_usuario = ejecutar_login()

        if datos_usuario == "EXIT":
            break

        if datos_usuario:

            id_u, nombre_u, tipo_u, primer_ingreso = datos_usuario

            print(f"\n Acceso concedido. Bienvenido, {nombre_u}!")

            if tipo_u == 1:

                while True:

                    print("\n[MODO ADMINISTRADOR]")
                    print("1. Sincronizar libros con la API")
                    print("2. Gestionar Usuarios")
                    print("3. Ver últimos 5 libros en sistema")
                    print("4. Cerrar Sesión")

                    op_admin = input("\nSelecciona una opción: ")

                    if op_admin == '1':
                        importar_desde_api()

                    elif op_admin == '2':
                        gestionar_usuarios()

                    elif op_admin == '3':

                        db = conectar()
                        cursor = db.cursor()

                        cursor.execute(
                            "SELECT titulo FROM libros ORDER BY id_libro DESC LIMIT 5"
                        )

                        for lib in cursor.fetchall():
                            print(f"• {lib[0]}")

                        db.close()

                    elif op_admin == '4':
                        break

            else:

                if primer_ingreso == 1:
                    alimentar_motor_usuario(id_u)

                else:
                    mostrar_recomendaciones(id_u)

            input("\nPresiona Enter para continuar...")

        else:
            print("\n Usuario o contraseña incorrectos.")


