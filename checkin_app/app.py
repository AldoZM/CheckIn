from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Thread
import time

# Solo se importa si se está en Raspberry Pi
try:
    from mfrc522 import SimpleMFRC522
    lector_rfid_disponible = True
except ImportError:
    lector_rfid_disponible = False

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checkin.db'
app.config['SECRET_KEY'] = 'secreto'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    usuario = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    rol = db.Column(db.String(10))
    rfid_uid = db.Column(db.String(20), unique=True)

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    hora = db.Column(db.DateTime, default=datetime.now)
    nombre = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    if current_user.rol == 'admin':
        registros_por_usuario = {}
        usuarios = Usuario.query.all()
        for usuario in usuarios:
            if usuario.rol != 'admin':
                registros = CheckIn.query.filter_by(usuario_id=usuario.id).order_by(CheckIn.hora.desc()).limit(5).all()
                registros_por_usuario[usuario.nombre] = registros
        return render_template('admin.html', registros_por_usuario=registros_por_usuario, usuarios=usuarios)
    else:
        checkins = CheckIn.query.filter_by(usuario_id=current_user.id).order_by(CheckIn.hora.desc()).limit(10).all()
        return render_template('index.html', checkins=checkins)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(usuario=request.form['usuario']).first()
        if usuario and check_password_hash(usuario.password, request.form['password']):
            login_user(usuario)
            return redirect(url_for('index'))
        return render_template('login.html', error="Credenciales incorrectas")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/checkin', methods=['POST'])
@login_required
def checkin():
    nuevo_checkin = CheckIn(usuario_id=current_user.id, nombre=current_user.nombre)
    db.session.add(nuevo_checkin)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/crear_usuario', methods=['POST'])
@login_required
def crear_usuario():
    if current_user.rol != 'admin':
        return "No autorizado", 403

    nombre = request.form['nombre']
    usuario = request.form['usuario']
    password = generate_password_hash(request.form['password'])
    uid = request.form['uid']

    if Usuario.query.filter_by(rfid_uid=uid).first():
        return "❌ El UID ya está asignado a otro trabajador.\nPor favor, usa otro tag.", 400

    nuevo_usuario = Usuario(
        nombre=nombre,
        usuario=usuario,
        password=password,
        rol='trabajador',
        rfid_uid=uid
    )
    db.session.add(nuevo_usuario)
    db.session.commit()
    return "✅ Usuario creado exitosamente", 200

@app.route('/eliminar_usuario/<int:usuario_id>')
@login_required
def eliminar_usuario(usuario_id):
    if current_user.rol != 'admin':
        return "No autorizado", 403
    usuario = Usuario.query.get(usuario_id)
    if usuario and usuario.rol != 'admin':
        db.session.delete(usuario)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/asignar_uid/<int:usuario_id>', methods=['POST'])
@login_required
def asignar_uid(usuario_id):
    if current_user.rol != 'admin':
        return "No autorizado", 403

    uid = request.form.get('uid')
    existente = Usuario.query.filter_by(rfid_uid=uid).first()
    if existente and existente.id != usuario_id:
        return "⚠️ Error: Este UID ya está asignado a otro trabajador.", 400

    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.rfid_uid = uid
        db.session.commit()
        return "UID asignado exitosamente", 200

    return "Usuario no encontrado", 404

@app.route('/leer_uid')
def leer_uid():
    if not lector_rfid_disponible:
        return "RFID no disponible", 500
    try:
        reader = SimpleMFRC522()
        uid, _ = reader.read()
        return str(uid)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/crear_admin_temp')
def crear_admin_temp():
    existente = Usuario.query.filter_by(usuario='admin1').first()
    if existente:
        return "⚠️ El usuario admin1 ya existe"

    admin = Usuario(
        nombre="Administrador 1",
        usuario="admin1",
        password=generate_password_hash("1234"),
        rol="admin"
    )
    db.session.add(admin)
    db.session.commit()
    return "✅ Usuario admin1 creado con contraseña 1234"

# Hilo para lectura continua del tag
def lector_rfid():
    if not lector_rfid_disponible:
        print("⚠️ Lector RFID no disponible (no en Raspberry Pi o módulo no conectado).")
        return
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()
    print("📡 Esperando tags para check-in automático...")
    while True:
        try:
            uid, _ = reader.read()
            print(f"🎫 UID detectado: {uid}")
            usuario = Usuario.query.filter_by(rfid_uid=str(uid)).first()
            if usuario:
                nuevo_checkin = CheckIn(usuario_id=usuario.id, nombre=usuario.nombre)
                db.session.add(nuevo_checkin)
                db.session.commit()
                print(f"✅ Check-in registrado para: {usuario.nombre}")
            else:
                print("❌ UID no registrado.")
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Error al leer tag: {e}")
            time.sleep(2)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if lector_rfid_disponible:
            hilo_rfid = Thread(target=lector_rfid, daemon=True)
            hilo_rfid.start()
    app.run(debug=True, host='0.0.0.0')
