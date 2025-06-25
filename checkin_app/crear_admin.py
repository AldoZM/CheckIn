from app import app
from models import db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    if not Usuario.query.filter_by(usuario="admin1").first():
        nuevo_admin = Usuario(
            nombre="Administrador",
            usuario="admin1",
            password=generate_password_hash("1234"),
            rol="admin"
        )
        db.session.add(nuevo_admin)
        db.session.commit()
        print("? Admin creado exitosamente")
    else:
        print("?? El admin ya existe")
