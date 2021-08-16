from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint

subs = db.Table('subs',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('kurs_id', db.Integer, db.ForeignKey('kurs.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    role = db.Column(db.Integer, default = 0)
    unvan = db.Column(db.String(40))
    adres = db.Column(db.String(50))
    telefon = db.Column(db.String(12))
    github = db.Column(db.String(40))
    twitter = db.Column(db.String(40))
    instagram = db.Column(db.String(40))
    linkedin = db.Column(db.String(40))
    subscriptions = db.relationship('Kurs', secondary = 'subs', backref = db.backref('subscribers', lazy = 'dynamic'))
    kurs_yorumlar = db.relationship('KursYorum')
    ders_yorumlar = db.relationship('DersYorum')
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    
    def __repr__(self):
        return 'User(name=%s, role=%d)' % self.first_name, self.role

class Egitmen(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True, nullable = False)
    ozgecmis = db.Column(db.String(1000))
    age = db.Column(db.Integer)
    verilen_kurslar = db.relationship('Kurs')

class Kurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(200))
    kategori = db.Column(db.String(200))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    kisa_aciklama = db.Column(db.String(100), nullable = True)
    uzun_aciklama = db.Column(db.String(2000), nullable = True)
    dersler = db.relationship('Ders')
    yorumlar = db.relationship('KursYorum')
    egitmen_id = db.Column(db.Integer, db.ForeignKey('egitmen.id'))
    #subscribers Kurs.subscribers
    def __repr__(self):
        return 'Kurs(name=%s, egitmen=%d)' % (self.isim,self.egitmen_id)

class Ders(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    video_url = db.Column(db.String(1000))
    baslik = db.Column(db.String(100), nullable = False)
    aciklama = db.Column(db.String(100))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    kurs_id = db.Column(db.Integer, db.ForeignKey('kurs.id'))

class KursYorum(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    icerik = db.Column(db.String(100)) 
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    puan = db.Column(db.Integer, CheckConstraint('puan>0 AND puan<=5'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    kurs_id = db.Column(db.Integer, db.ForeignKey('kurs.id'), nullable = False)
    parent_yorum = db.Column(db.Integer, db.ForeignKey('kurs_yorum.id'), nullable = True)
    children = db.relationship('KursYorum')

class DersYorum(db.Model):   
    id = db.Column(db.Integer, primary_key = True)
    baslik = db.Column(db.String(25)) 
    icerik = db.Column(db.String(100)) 
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    ders_id = db.Column(db.Integer, db.ForeignKey('ders.id'), nullable = False)
    parent_yorum = db.Column(db.Integer, nullable = True)




