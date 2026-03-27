import mysql.connector
def get_connection():
# Creamos una conexión a MySQL
    return mysql.connector.connect(
        host="localhost", # Servidor
        user="root", # Usuario
        password="090806", # Contraseña
        database="flask_db" # Base de datos
    )