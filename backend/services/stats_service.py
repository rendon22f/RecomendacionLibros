import pandas as pd
from backend.database.connection import conectar


def obtener_estadisticas_plataforma():
    try:
        db = conectar()

        # Carga de datos desde MySQL a DataFrames de Pandas
        df_puntuaciones = pd.read_sql("SELECT * FROM puntuacion", db)
        df_libros = pd.read_sql("SELECT * FROM libros", db)
        df_usuarios = pd.read_sql("SELECT * FROM usuarios", db)

        db.close()


        if df_puntuaciones.empty:
            return {
                "total_usuarios_activos": int(df_usuarios[df_usuarios['tipo'] == 2].shape[0]),
                "top_5_libros": [],
                "generos_preferidos": [],
                "actividad_por_usuario": []
            }


        total_usuarios = int(df_usuarios[df_usuarios['tipo'] == 2].shape[0])


        df_merged_libros = pd.merge(df_puntuaciones, df_libros, on="id_libro")
        df_merged_usuarios = pd.merge(df_puntuaciones, df_usuarios, on="id_usuario")


        df_libros_agrupados = df_merged_libros.groupby(["id_libro", "titulo", "autor"]).agg(
            calificacion_promedio=('calificacion', 'mean'),
            total_votos=('calificacion', 'count')
        ).reset_index()

        top_5 = df_libros_agrupados.sort_values(by=["calificacion_promedio", "total_votos"], ascending=False).head(5)
        top_5_list = top_5.to_dict(orient="records")


        df_generos = df_merged_libros.groupby("genero").agg(
            total_calificaciones=('calificacion', 'count'),
            calificacion_media=('calificacion', 'mean')
        ).reset_index()

        df_generos = df_generos.sort_values(by="total_calificaciones", ascending=False)
        generos_list = df_generos.to_dict(orient="records")


        df_usuarios_agrupados = df_merged_usuarios.groupby("username").agg(
            libros_calificados=('calificacion', 'count')
        ).reset_index()

        df_usuarios_agrupados = df_usuarios_agrupados.sort_values(by="libros_calificados", ascending=False)
        usuarios_list = df_usuarios_agrupados.to_dict(orient="records")

        return {
            "total_usuarios_activos": total_usuarios,
            "top_5_libros": top_5_list,
            "generos_preferidos": generos_list,
            "actividad_por_usuario": usuarios_list
        }

    except Exception as e:
        return {"error": str(e)}