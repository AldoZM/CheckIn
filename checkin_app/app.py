from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from collections import defaultdict
import os

app = Flask(__name__)
app.secret_key = 'clave-secreta-muy-fuerte'

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'checkins.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(10), nullable=False)  # 'admin' o 'trabajador'

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    hora = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(usuario=request.form['usuario']).first()
        if usuario and check_password_hash(usuario.password, request.form['password']):
            login_user(usuario)
            if usuario.rol == 'admin':
                return redirect('/admin')
            else:
                return redirect('/')
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if current_user.rol != 'trabajador':
        return redirect('/admin')
    registros = Registro.query.order_by(Registro.hora.desc()).all()
    return render_template('index.html', checkins=registros)

@app.route('/checkin', methods=['POST'])
@login_required
def checkin():
    if current_user.rol != 'trabajador':
        return redirect('/admin')
    nuevo = Registro(nombre=current_user.nombre)
    db.session.add(nuevo)
    db.session.commit()
    return redirect('/')

@app.route('/admin')
@login_required
def admin():
    if current_user.rol != 'admin':
        return redirect('/')

    registros = Registro.query.order_by(Registro.hora.desc()).all()
    usuarios = Usuario.query.order_by(Usuario.nombre).all()

    registros_por_usuario = defaultdict(list)
    for r in registros:
        registros_por_usuario[r.nombre].append(r)

    return render_template(
        'admin.html',
        checkins=registros,
        usuarios=usuarios,
        registros_por_usuario=registros_por_usuario
    )

@app.route('/crear_usuario', methods=['POST'])
@login_required
def crear_usuario():
    if current_user.rol != 'admin':
        return redirect('/')

    nombre = request.form['nombre']
    usuario = request.form['usuario']
    password = generate_password_hash(request.form['password'])

    if Usuario.query.filter_by(usuario=usuario).first():
        return "Ese nombre de usuario ya existe."

    nuevo = Usuario(nombre=nombre, usuario=usuario, password=password, rol='trabajador')
    db.session.add(nuevo)
    db.session.commit()
    return redirect('/admin')

@app.route('/eliminar_usuario/<int:id>')
@login_required
def eliminar_usuario(id):
    if current_user.rol != 'admin':
        return redirect('/')

    usuario = Usuario.query.get_or_404(id)

    if usuario.rol == 'admin' or usuario.id == current_user.id:
        return "No puedes eliminar a este usuario."

    db.session.delete(usuario)
    db.session.commit()
    return redirect('/admin')

# Inicializar base de datos y administradores
with app.app_context():
    db.create_all()

    if not Usuario.query.filter_by(usuario='admin1').first():
        admin1 = Usuario(
            nombre='Administrador 1',
            usuario='admin1',
            password=generate_password_hash('adminpass1'),
            rol='admin'
        )
        db.session.add(admin1)

    if not Usuario.query.filter_by(usuario='admin2').first():
        admin2 = Usuario(
            nombre='Administrador 2',
            usuario='admin2',
            password=generate_password_hash('adminpass2'),
            rol='admin'
        )
        db.session.add(admin2)

    db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
