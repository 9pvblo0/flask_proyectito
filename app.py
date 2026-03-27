from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from functools import wraps
from db import get_connection
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt
)
from flask import jsonify
from flask_cors import CORS

app = Flask(__name__)
from db import get_connection
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

def inicializar_bd():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios_sistema (
        id INT AUTO_INCREMENT PRIMARY KEY,
        correo VARCHAR(255),
        nombres VARCHAR(255),
        apellidos VARCHAR(255),
        clave TEXT,
        rol VARCHAR(50)
    )
    """)

    cursor.execute(
        "SELECT * FROM usuarios_sistema WHERE correo = %s",
        ("admin@test.com",)
    )

    usuario = cursor.fetchone()

    if not usuario:
        hash = bcrypt.generate_password_hash("123456").decode("utf-8")

        cursor.execute("""
        INSERT INTO usuarios_sistema
        (correo,nombres,apellidos,clave,rol)
        VALUES (%s,%s,%s,%s,%s)
        """,(
        "admin@test.com",
        "Admin",
        "Principal",
        hash,
        "administrador"
        ))

        conn.commit()

    conn.close()

inicializar_bd()
def crear_tablas_restantes():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255),
        email VARCHAR(255)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255),
        descripcion TEXT,
        estado INT DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inscripciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT,
        curso_id INT,
        fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

crear_tablas_restantes()

CORS(app) 
app.config["JWT_SECRET_KEY"] = "clave_super_segura_api"
app.config["JWT_IDENTITY_CLAIM"] = "sub"
jwt = JWTManager(app)

app.secret_key = "clave_secreta_segura"
bcrypt = Bcrypt(app)

@app.route('/', methods=['GET', 'POST'])
def inicio():
    #declaramos variable inicial vacio
    nombre = None

    # Si el formulario fue enviado
    if request.method == 'POST':
        # Capturamos el valor del input llamado "nombre"
        nombre = request.form['nombre']

    # Retornamos texto simple al navegador
    # Flask lo envía como respuesta HTTP
    #return "Hola Mundo desde Flask"
    return render_template('index.html', nombre=nombre)

# -------------------------------
# DECORADOR: LOGIN REQUERIDO
# -------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# DECORADOR: SOLO ADMIN
# -------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("rol") != "administrador":
            return "Acceso denegado", 403
        return f(*args, **kwargs)
    return decorated_function 

# Ruta login
 
@app.route("/login", methods=["GET", "POST"])
def login():

    # LOGIN TEMPORAL SOLO PARA PRIMER ACCESO
    if request.method == "POST":

        correo = request.form["correo"]
        clave = request.form["clave"]

        if correo == "admin@test.com" and clave == "123456":

            session["usuario_id"] = 1
            session["rol"] = "administrador"
            session["nombre"] = "Admin"

            return redirect(url_for("usuarios"))

        return "Credenciales incorrectas"

    return render_template("login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()

    correo = data.get("correo")
    clave = data.get("clave")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM usuarios_sistema WHERE correo = %s",
        (correo,)
    )
    usuario = cursor.fetchone()
    conn.close()

    if usuario and bcrypt.check_password_hash(usuario["clave"], clave):

        access_token = create_access_token(
            identity=str(usuario["id"]),  
            additional_claims={"rol": usuario["rol"]}
        )

        return jsonify(access_token=access_token)

    return jsonify({"msg": "Credenciales incorrectas"}), 401

@app.route("/api/usuarios", methods=["GET"])
def api_usuarios():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios")
    data = cursor.fetchall()
    conn.close()

    return jsonify(data)

@app.route("/api/cursos", methods=["GET"])
def api_cursos():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cursos WHERE estado = 1")
    data = cursor.fetchall()
    conn.close()

    return jsonify(data)

@app.route("/api/usuarios", methods=["POST"])
@jwt_required()
def api_crear_usuario():

    data = request.get_json()

    nombre = data.get("nombre")
    email = data.get("email")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (nombre, email) VALUES (%s, %s)",
        (nombre, email)
    )

    conn.commit()
    conn.close()

    return jsonify({"msg": "Usuario creado"}), 201

@app.route("/api/cursos", methods=["POST"])
@jwt_required()
def api_crear_curso():

    claims = get_jwt()

    if claims["rol"] != "administrador":
        return jsonify({"msg": "Solo administradores"}), 403

    data = request.get_json()

    nombre = data.get("nombre")
    descripcion = data.get("descripcion")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cursos (nombre, descripcion) VALUES (%s, %s)",
        (nombre, descripcion)
    )

    conn.commit()
    conn.close()

    return jsonify({"msg": "Curso creado"}), 201

@app.route("/api/inscripciones", methods=["POST"])
@jwt_required()
def api_inscripcion():

    data = request.get_json()

    usuario_id = data.get("usuario_id")
    curso_id = data.get("curso_id")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO inscripciones (usuario_id, curso_id) VALUES (%s, %s)",
        (usuario_id, curso_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"msg": "Inscripción registrada"}), 201

@app.route("/api/inscripciones", methods=["GET"])
def api_listar_inscripciones():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT i.id, u.nombre AS usuario, c.nombre AS curso, i.fecha_inscripcion
        FROM inscripciones i
        JOIN usuarios u ON i.usuario_id = u.id
        JOIN cursos c ON i.curso_id = c.id
    """)

    data = cursor.fetchall()
    conn.close()

    return jsonify(data)

# Ruta logout 
 
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

#para lectura de usuarios
@app.route('/usuarios')
def usuarios():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Consultamos todos los usuarios
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/nuevo')
def nuevo_usuario():
    return render_template('usuarios_form.html')

@app.route('/usuarios/editar/<int:id>')
def editar_usuario(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    return render_template('usuarios_form.html', usuario=usuario)

@app.route('/usuarios/actualizar/<int:id>', methods=['POST'])
def actualizar_usuario(id):
    nombre = request.form['nombre']
    email = request.form['email']
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    "UPDATE usuarios SET nombre=%s, email=%s WHERE id=%s",
    (nombre, email, id)
    )
    conn.commit()
    return redirect('/usuarios')

@app.route('/usuarios/eliminar/<int:id>')
def eliminar_usuario(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conn.commit()
    return redirect('/usuarios')

@app.route('/usuarios/guardar', methods=['POST'])
def guardar_usuario():
    nombre = request.form['nombre']
    email = request.form['email']
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    "INSERT INTO usuarios (nombre, email) VALUES (%s, %s)",
    (nombre, email)
    )
    conn.commit()
    return redirect('/usuarios')


# REGISTRO DE USUARIOS DE SISTEMA
@app.route("/sistema/usuarios/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def usuarios_sistema_nuevo():
    if request.method == "POST":
        correo = request.form["correo"]
        nombres = request.form["nombres"]
        apellidos = request.form["apellidos"]
        rol = request.form["rol"]

        clave_hash = bcrypt.generate_password_hash("123456").decode("utf-8")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios_sistema
            (correo, nombres, apellidos, clave, rol)
            VALUES (%s, %s, %s, %s, %s)
        """, (correo, nombres, apellidos, clave_hash, rol))

        conn.commit()
        conn.close()
        return redirect(url_for("usuarios"))

    return render_template("usuarios_sistema_form.html")


#CAMBIO DE CONTRASEÑA (USUARIO LOGUEADO) 
@app.route("/cambiar_clave", methods=["GET", "POST"])
@login_required
def cambiar_clave():
    if request.method == "POST":
        nueva = request.form["nueva"]

        clave_hash = bcrypt.generate_password_hash(nueva).decode("utf-8")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios_sistema
            SET clave = %s
            WHERE id = %s
        """, (clave_hash, session["usuario_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for("usuarios"))

    return render_template("cambiar_clave.html")


#Ruta listar inscripciones 
@app.route('/inscripciones')
def inscripciones():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT i.id, u.nombre AS usuario, c.nombre AS curso, i.fecha_inscripcion
        FROM inscripciones i
        JOIN usuarios u ON i.usuario_id = u.id
        JOIN cursos c ON i.curso_id = c.id
    """)

    data = cursor.fetchall()
    return render_template('inscripciones.html', inscripciones=data) 


#RUTA PARA INSCRIPCIONES NUEVAS  

# INSCRIBIR ALUMNO EN CURSO
# (ADMIN Y ASISTENTE)

@app.route("/inscripciones/nueva", methods=["GET", "POST"])
@login_required
def inscripcion_nueva():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener alumnos
    cursor.execute("SELECT id, nombre FROM usuarios")
    alumnos = cursor.fetchall()

    # Obtener cursos
    cursor.execute("SELECT id, nombre FROM cursos")
    cursos = cursor.fetchall()

    # Si el formulario fue enviado
    if request.method == "POST":
        alumno_id = request.form["alumno_id"]
        curso_id = request.form["curso_id"]

        cursor.execute("""
            INSERT INTO inscripciones (usuario_id, curso_id)
            VALUES (%s, %s)
        """, (alumno_id, curso_id))

        conn.commit()
        conn.close()
        return redirect(url_for("inscripciones"))

    conn.close()
    return render_template(
        "inscripcion_form.html",
        alumnos=alumnos,
        cursos=cursos
    )

#CURSOS
@app.route('/cursos')
@login_required
#@admin_required
def cursos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cursos WHERE estado = 1")
    cursos = cursor.fetchall()
    cursor.close()
    return render_template('cursos/index.html', cursos=cursos)


#NUEVO CURSO
@app.route('/cursos/nuevo')
@login_required
@admin_required
def nuevo_curso():
    return render_template('cursos/nuevo.html')

#GUARDAR CURSO
@app.route('/cursos/guardar', methods=['POST'])
@login_required
@admin_required
def guardar_curso():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "INSERT INTO cursos (nombre, descripcion) VALUES (%s, %s)",
        (nombre, descripcion)
    )
    conn.commit()
    cursor.close()

    flash('Curso registrado correctamente', 'success')
    return redirect(url_for('cursos'))



if __name__ == '__main__':
# Inicia el servidor de desarrollo
# debug=True permite ver errores detallados
    app.run(debug=True)

from db import get_connection
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def crear_admin_si_no_existe():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios_sistema WHERE correo = %s", ("admin@test.com",))
    usuario = cursor.fetchone()

    if not usuario:
        clave_hash = bcrypt.generate_password_hash("123456").decode("utf-8")

        cursor.execute("""
            INSERT INTO usuarios_sistema (correo, nombres, apellidos, clave, rol)
            VALUES (%s, %s, %s, %s, %s)
        """, ("admin@test.com", "Admin", "Principal", clave_hash, "administrador"))

        conn.commit()

    conn.close()

crear_admin_si_no_existe()