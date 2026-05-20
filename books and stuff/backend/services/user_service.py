from backend.database.connection import conectar

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