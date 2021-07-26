from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

subs = db.Table('subs',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('kurs_id', db.Integer, db.ForeignKey('kurs.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Integer, default = 0, onupdate = 1)
    subscriptions = db.relationship('Kurs', secondary = 'subs', backref = db.backref('subscribers', lazy = 'dynamic'))

class Kurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(200))
    kategori = db.Column(db.String(200))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    aciklama = db.Column(db.String(1000), nullable = True)
    dersler = db.relationship('Ders')
    egitmen_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #subscribers Kurs.subscribers

class Ders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_url = db.Column(db.String(1000))
    ders_baslik = db.Column(db.String(100), nullable = False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    kurs_id = db.Column(db.Integer, db.ForeignKey('kurs.id'))

