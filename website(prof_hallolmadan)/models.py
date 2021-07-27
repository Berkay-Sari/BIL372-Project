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
    role = db.Column(db.Integer, default = 0)
    #image_file = db.Column(db.String(20), default = 'default.jpg')
    subscriptions = db.relationship('Kurs', secondary = 'subs', backref = db.backref('subscribers', lazy = 'dynamic'))
    def __repr__(self):
        return 'User(name=%s, role=%d)' % self.first_name, self.role

class Egitmen(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True, nullable = False)


class Kurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(200))
    kategori = db.Column(db.String(200))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    aciklama = db.Column(db.String(100), nullable = True)
    # kisa_aciklama = db.Column(db.String(100), nullable = True)
    # uzun_aciklama = db.Column(db.String(2000), nullable = True)
    dersler = db.relationship('Ders')
    egitmen_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #subscribers Kurs.subscribers
    def __repr__(self):
        return 'Kurs(name=%s, egitmen=%d)' % (self.isim,self.egitmen_id)

class Ders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_url = db.Column(db.String(1000))
    ders_baslik = db.Column(db.String(100), nullable = False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    kurs_id = db.Column(db.Integer, db.ForeignKey('kurs.id'))

