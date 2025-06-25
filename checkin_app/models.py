from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    usuario = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    rol = db.Column(db.String(20))
    rfid_uid = db.Column(db.String(100), unique=True)

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    hora = db.Column(db.DateTime, default=datetime.utcnow)
