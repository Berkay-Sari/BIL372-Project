from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from .models import Kurs, User, Egitmen, KursYorum, DersYorum, Ders
from . import db, app
import json
import os
import secrets
from PIL import Image


views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        """
        kurs = request.form.get('kurs')
        new_kurs = Kurs(kategori=kurs)
        db.session.add(new_kurs)
        new_kurs.subscribers.append(current_user)
        db.session.commit()
        flash('Kurs eklendi!', category='success')
        """
        looking_for = request.form.get('arama')
        
        return redirect(url_for('views.arama', looking_for = looking_for))

    result = db.engine.execute("SELECT Kurs.id,isim,kategori,first_name,last_name FROM Kurs, User WHERE Kurs.egitmen_id = User.id")
    
    return render_template("home.html", user=current_user, query = result)
          
@views.route('/arama/<looking_for>', methods=['GET', 'POST'])
@login_required
def arama(looking_for):
    kurs_sonuclari = db.engine.execute("SELECT * FROM Kurs WHERE isim LIKE '" + looking_for + "' OR kategori LIKE '" + looking_for +"'")
    return render_template("arama.html", user=current_user, query=kurs_sonuclari)

@views.route('/kurslarım', methods=['GET', 'POST'])
@login_required
def kurslarim():
    kurslarim = current_user.subscriptions
    egitmenler = []
    for kurs in kurslarim:
        egitmen = User.query.filter_by(id=kurs.egitmen_id).first()
        egitmenler.append(egitmen)

    egitmenler = list(dict.fromkeys(egitmenler))
    return render_template("kurslarım.html", user=current_user, kurslar = kurslarim, egitmenler = egitmenler)

@views.route('/kurs_profil/<int:id>', methods=['GET', 'POST'])
@login_required
def kurs_profil(id):
    kurs = Kurs.query.get_or_404(id)
    egitmen_id = kurs.egitmen_id
    egitmen = User.query.get_or_404(egitmen_id) 
    dersler = kurs.dersler
    return render_template("kurs_profil.html", user=current_user, kurs = kurs, egitmen = egitmen, dersler = dersler)

@views.route('/ders/<int:id>', methods=['GET', 'POST'])
@login_required
def ders(id):
    ders = Ders.query.get_or_404(id)
    kurs = Kurs.query.get_or_404(ders.kurs_id)
    egitmen_id = kurs.egitmen_id
    egitmen = User.query.get_or_404(egitmen_id) 
    return render_template("ders.html", user=current_user, ders = ders, kurs = kurs, egitmen = egitmen)

@views.route('/hesap_ayarları', methods=['GET', 'POST'])
def hesap_ayarları():
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        
        if user and user.id != current_user.id:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            current_user.email = email
            current_user.password = generate_password_hash(password1, method='sha256')
            db.session.commit()
            flash('Hesap ayarları güncellendi!', category='success')
            return redirect('/profil/' + str(current_user.id))

    return render_template("hesap_ayarları.html", user = current_user)
    
@views.route('/profil_ayarları', methods=['GET', 'POST'])
def update_profil():
    if request.method == 'POST':
        isim = request.form.get('firstName')
        soy_isim = request.form.get('lastName')
        unvan = request.form.get('Ünvan')
        tel = request.form.get('Tel')
        adres = request.form.get('adres')
        github = request.form.get('github')
        linkedin = request.form.get('linkedin')
        twitter = request.form.get('twitter')
        facebook = request.form.get('facebook')
        instagram = request.form.get('instagram')
        youtube = request.form.get('youtube')
        
        ozgecmis = "ozgecmis"
        if current_user.role == 1:
            ozgecmis = request.form.get('ozgecmis')
        
        if len(isim) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(soy_isim) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif not(str.isdecimal(tel)):
            flash('Telefon numarası harf içermemeli.', category='error')
        elif len(tel) != 10:
            flash('Telefon numarası 10 rakamdan oluşmalı.', category='error')
        else:
            current_user.first_name = isim
            current_user.last_name = soy_isim
            current_user.unvan = unvan
            current_user.telefon = tel
            current_user.adres = adres
            current_user.github = github
            current_user.twitter = twitter
            current_user.linkedin = linkedin
            current_user.instagram = instagram
            if current_user.role == 1:
                egitmen = Egitmen.query.filter_by(id=current_user.id).first()
                egitmen.ozgecmis = ozgecmis
            db.session.commit()
            flash('Profil ayarları güncellendi!', category='success')
            return redirect('/profil/' + str(current_user.id))
    egitmen = Egitmen.query.filter_by(id=current_user.id).first()
    return render_template("profil_ayarları.html", user = current_user, egitmen = egitmen)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def save_picture(form_picture):
    random_hex = secrets.token_hex(8) #dosya isimlerinde karisiklik yasanmamasi icin
    _, f_ext = os.path.splitext(form_picture.filename) #dosyanin extensionunu alıyor yani png jpg gibi
    picture_fn = random_hex + f_ext #artik resim dosyasinin ismi unique ve extensionu da var misal 1865csd5f8sd.jpg gibisinden
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) # image icin roottan başlayan path olusturuyor

    output_size = (125, 125)  #burasi ve asagisi resmi resizelayabilmek icin var bunun icin package called PILLOW kullanıyoruz
    i = Image.open(form_picture)  #pip install PIL falan yapmak gerekiyor yani
    i.thumbnail(output_size)
    i.save(picture_path) #pathe resize edilmis resmi kaydediyor yani static/profilepics klasörüne

    return picture_fn  #resim dosyasinin ismini dönüyor

@views.route('/foto_ayarları', methods=['GET', 'POST'])
def update_foto():
    if request.method == 'POST':
        img = request.files['image']
        if img.filename == '':
            flash('Profil resmi için dosya seçilmedi!', category ='error')
            return redirect(request.url)
        if img and allowed_file(img.filename):
            filename = save_picture(img)
            current_user.image_file = filename
            db.session.commit()
            flash('Profil resmi değiştirildi!', category ='success')
            return render_template("foto_ayarları.html", user = current_user)
    return render_template("foto_ayarları.html", user = current_user)

@views.route('/profil/<int:id>', methods=['GET', 'POST'])
@login_required
def profil(id):
    self_profil = 1
    user = User.query.get_or_404(id)
    kurslar = user.subscriptions
    if user.id != current_user.id:
        self_profil = 0
    if user.role == 1:
        egitmen = Egitmen.query.filter_by(id=user.id).first()
        verilen_kurslar = db.engine.execute("SELECT Kurs.id,isim,kategori,first_name,last_name FROM Kurs, User WHERE Kurs.egitmen_id = User.id")
        return render_template("profil.html", self_profil = self_profil, user = user, egitmen = egitmen, verilen_kurslar = verilen_kurslar, kurslar = kurslar)

    return render_template("profil.html", self_profil = self_profil, user = user, kurslar = kurslar)

    
@views.route('/delete-note', methods=['POST'])
def delete_note():
    kurs = json.loads(request.data)
    noteId = kurs['noteId']
    kurs = Kurs.query.get(noteId)
    db.session.delete(kurs)
    db.session.commit()

    return jsonify({})
