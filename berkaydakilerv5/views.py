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
        if looking_for:
            return redirect(url_for('views.arama', looking_for = looking_for))
    #BEST 5 KURS
    result = db.engine.execute("SELECT Kurs.id,isim,kategori,first_name,last_name FROM Kurs, User WHERE Kurs.egitmen_id = User.id AND Kurs.id IN (SELECT kurs_id FROM subs GROUP BY kurs_id ORDER BY COUNT(*) DESC LIMIT 5)")
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])

    return render_template("home.html", user=current_user, query = result, kategoriler = kategoriler)
          
@views.route('/arama/<looking_for>', methods=['GET', 'POST'])
@login_required
def arama(looking_for):
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])
    if request.method == 'POST':
        looking_for = request.form.get('arama')
        if looking_for:
            return redirect(url_for('views.arama', looking_for = looking_for))
    kurs_sonuclari = db.engine.execute("SELECT isim, kisa_aciklama, kategori, first_name, Kurs.date, Kurs.id AS id FROM Kurs,User WHERE Kurs.egitmen_id = User.id AND kategori LIKE \"%" + looking_for + "%\" OR isim LIKE \"%" + looking_for +"%\"")
    #sorted_by_isim = sorted(kurs_sonuclari, key=lambda Kurs: Kurs.isim)
    return render_template("arama.html", user=current_user, query=kurs_sonuclari, kategoriler = kategoriler)

@views.route('/kurslarım', methods=['GET', 'POST'])
@login_required
def kurslarim():
    if request.method == 'POST':
        looking_for = request.form.get('arama')
        if looking_for:
            return redirect(url_for('views.arama', looking_for = looking_for))
    kurslarim = current_user.subscriptions
    egitmenler = []
    for kurs in kurslarim:
        egitmen = User.query.filter_by(id=kurs.egitmen_id).first()
        egitmenler.append(egitmen)
    
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])
    
    egitmenler = list(dict.fromkeys(egitmenler))
    return render_template("kurslarım.html", user=current_user, kurslar = kurslarim, egitmenler = egitmenler, kategoriler = kategoriler)

@views.route('/egitmenkurslari', methods=['GET', 'POST'])
@login_required
def egitmenkurslari():
    egitmen = Egitmen.query.filter_by(id=current_user.id).first()
    kurslarim = egitmen.verilen_kurslar

    return render_template("egitmenkurslari.html", user=current_user, egitmen = egitmen, kurslar = kurslarim)


@views.route('/yeni_kurs', methods=['GET', 'POST'])
@login_required
def yeni_kurs():
    if request.method == 'POST':
        kategori = request.form.get('kategori')
        isim = request.form.get('kurs_baslik')
        kisa_aciklama = request.form.get('kısa_açıklama')
        uzun_aciklama = request.form.get('uzun_açıklama')
        kurs = Kurs.query.filter_by(isim=isim).first()
        if kurs:
            flash('Aynı isimde bir kurs bulunmaktadır.', category='error')
        else:
            new_kurs = Kurs(isim=isim,kategori=kategori, kisa_aciklama = kisa_aciklama, uzun_aciklama= uzun_aciklama, egitmen_id = current_user.id)
            db.session.add(new_kurs)
            db.session.commit()
            return redirect('/ders_duzenle/' + str(new_kurs.id)) 
        
    egitmen = Egitmen.query.filter_by(id=current_user.id).first()
    kurslarim = None
    if egitmen:
        kurslarim = egitmen.verilen_kurslar
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])

    return render_template("yeni_kurs.html", user=current_user, egitmen = egitmen, kurslar = kurslarim, kategoriler = kategoriler)

@views.route('/kurs_profil/<int:id>', methods=['GET', 'POST'])
@login_required
def kurs_profil(id):
    if request.method == 'POST':
        rating = request.form.get('rating')
        if not rating:
            flash('Yaptığınız yoruma puan vermediniz', category='error')
        else:
            yorum = request.form.get('yorum')
            new_yorum = KursYorum(icerik=yorum, puan=rating, user_id = current_user.id, kurs_id = id)
            x = KursYorum.query.filter_by(user_id = current_user.id).first()
            if x:
                x.icerik = yorum
                x.puan = rating
            else:
                db.session.add(new_yorum)
            
            db.session.commit()
            flash('Yorum eklendi!', category='success')

    kurs = Kurs.query.get_or_404(id)
    egitmen_id = kurs.egitmen_id
    egitmen = User.query.get_or_404(egitmen_id) 
    dersler = kurs.dersler
    kurs.uzun_aciklama = row_duzenleme(kurs.uzun_aciklama)
    result = db.engine.execute("SELECT icerik,Kurs_yorum.date,puan,first_name,last_name,image_file FROM User, Kurs_yorum WHERE Kurs_yorum.user_id = User.id AND Kurs_yorum.kurs_id =" +str(id) +" GROUP BY User.id ORDER BY Kurs_yorum.date ASC")
    result2 = db.engine.execute("SELECT AVG(puan) AS ort FROM Kurs_yorum WHERE Kurs_yorum.kurs_id=" +str(id))
    ort_puan = None
    for x in result2:
        a = str(x)
        end = len(a)
        ort_puan = a[1:end-2]

    return render_template("kurs_profil.html", user=current_user, kurs = kurs, egitmen = egitmen, dersler = dersler, yorumlar = result, puan = ort_puan)

def row_duzenleme(s):
    yeni_string = ""
    a = 0
    for i in s:
        yeni_string += i
        if a == 122:
            yeni_string += "\n"
            a = 0
        a = a+1
    return yeni_string

@views.route('/kurs_ayarlari/<int:id>')
@login_required
def kurs_ayarla(id):
    kurs = Kurs.query.filter_by(id = id).first()
    return render_template("kurs_ayarlari.html", kurs = kurs)

@views.route('/kursa_kaydol/<int:id>')
@login_required
def kaydol(id):
    kurs = Kurs.query.filter_by(id=id).first()
    kurs.subscribers.append(current_user)
    db.session.commit()
    flash('Kurs eklendi!', category='success')
    return redirect('/kurs_profil/' + str(id))

@views.route('/ders/<int:id>', methods=['GET', 'POST'])
@login_required
def ders(id):
    ders = Ders.query.get_or_404(id)
    kurs = Kurs.query.get_or_404(ders.kurs_id)
    egitmen_id = kurs.egitmen_id
    egitmen = User.query.get_or_404(egitmen_id) 
    #result = db.engine.execute("SELECT User.id AS id, Ders_yorum.id AS key, first_name, last_name, icerik, baslik, image_file, ders_yorum.date FROM Ders_yorum,User WHERE Ders_yorum.ders_id =" + str(id) + " AND ders_yorum.user_id = User.id") 
    
    if request.method == 'POST':
        baslik = request.form.get('soru_baslik')
        icerik = request.form.get('soru_aciklama')
        if not icerik:
            flash("İçerik boş olamaz!", category = 'error')
            return render_template("ders.html", user=current_user, ders = ders, kurs = kurs, egitmen = egitmen)
        
        new_ders_yorum = DersYorum(baslik=baslik, icerik=icerik, ders_id=id, user_id = current_user.id)
        db.session.add(new_ders_yorum)
        db.session.commit()
        result = db.engine.execute("SELECT User.id AS id, Ders_yorum.id AS key, first_name, last_name, icerik, baslik, image_file, ders_yorum.date FROM Ders_yorum,User WHERE Ders_yorum.ders_id =" + str(id) + " AND ders_yorum.user_id = User.id") 
        #if yorum_id:
        #   return redirect('/ders_yoruma_cvp/' + str(yorum_id))
    result = db.engine.execute("SELECT User.id AS id, Ders_yorum.id AS key, first_name, last_name, icerik, baslik, image_file, ders_yorum.date FROM Ders_yorum,User WHERE Ders_yorum.ders_id =" + str(id) + " AND ders_yorum.user_id = User.id")
    kursa_ait_dersler = db.engine.execute("SELECT * FROM Ders WHERE kurs_id =" +str(kurs.id))
    return render_template("ders.html", user=current_user, ders = ders, kurs = kurs, egitmen = egitmen, query = result, kursa_ait_dersler = kursa_ait_dersler)

@views.route('/ders_yoruma_cvp/<int:id>', methods=['GET', 'POST'])
@login_required
def ders_yoruma_cvp(id):
    if request.method == 'POST':
        icerik = request.form.get('soru_aciklama')   
        if icerik:
            new_ders_yorum = DersYorum(icerik=icerik, ders_id=1, user_id = current_user.id, parent_yorum = id)
            db.session.add(new_ders_yorum)
            db.session.commit()
    baba = DersYorum.query.get_or_404(id)
    baba_user_id = baba.user_id
    baba_user = User.query.filter_by(id = baba_user_id).first()
    ders = Ders.query.get_or_404(baba.ders_id)
    kurs = Kurs.query.get_or_404(ders.kurs_id)
    egitmen_id = kurs.egitmen_id
    egitmen = User.query.get_or_404(egitmen_id) 
    kursa_ait_dersler = Ders.query.filter_by(id = kurs.id)
    
    childlar = db.engine.execute("SELECT User.id AS id, first_name, last_name, image_file, Ders_yorum.id AS key, icerik, ders_yorum.date FROM Ders_yorum, User WHERE User.id = Ders_yorum.user_id AND parent_yorum=" + str(id))
    
    return render_template("ders_yoruma_cvp.html", user=current_user, ders = ders, kurs = kurs, egitmen = egitmen, yorum_id = id, childlar = childlar, baba = baba, baba_user = baba_user, kursa_ait_dersler = kursa_ait_dersler)

@views.route('/ders_duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def ders_duzenle(id):
    kurs = Kurs.query.get_or_404(id)
    egitmen_id = kurs.egitmen_id
    egitmen = User.query.get_or_404(egitmen_id) 
    return render_template("ders_duzenle.html", user=current_user, kurs = kurs, egitmen = egitmen)


@views.route('/hesap_ayarları', methods=['GET', 'POST'])
@login_required
def hesap_ayarları():
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])
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

    return render_template("hesap_ayarları.html", user = current_user, kategoriler = kategoriler)
    
@views.route('/profil_ayarları', methods=['GET', 'POST'])
@login_required
def update_profil():
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])
    if request.method == 'POST':
        isim = request.form.get('firstName')
        if not isim: 
            isim = current_user.first_name
        soy_isim = request.form.get('lastName')
        if not soy_isim:
            soy_isim = current_user.last_name
        unvan = request.form.get('Ünvan')
        if not unvan:
            unvan = current_user.unvan
        tel = request.form.get('Tel')
        if not tel:
            tel = current_user.telefon
        adres = request.form.get('adres')
        if not adres:
            adres = current_user.adres
        github = request.form.get('github')
        if not github:
            github = current_user.github
        linkedin = request.form.get('linkedin')
        if not linkedin:
            linkedin = current_user.linkedin
        twitter = request.form.get('twitter')
        if not twitter:
            twitter = current_user.twitter
        facebook = request.form.get('facebook')
        instagram = request.form.get('instagram')
        if not instagram:
            instagram = current_user.instagram
        youtube = request.form.get('youtube')
        
        ozgecmis = "ozgecmis"
        if current_user.role == 1:
            ozgecmis = request.form.get('ozgecmis')
        
        if len(isim) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(soy_isim) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif tel and not(str.isdecimal(tel)):
            flash('Telefon numarası harf içermemeli.', category='error')
        elif tel and len(tel) != 10:
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
    return render_template("profil_ayarları.html", user = current_user, egitmen = egitmen, kategoriler = kategoriler)

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
@login_required
def update_foto():
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])
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
            return render_template("foto_ayarları.html", user = current_user, kategoriler = kategoriler)
    return render_template("foto_ayarları.html", user = current_user, kategoriler = kategoriler)

@views.route('/egitmen_ol', methods=['GET', 'POST'])
@login_required
def egitmen_ol():
    return render_template("egitmen_ol.html", user=current_user)

@views.route('/egitmen_yap/<int:id>', methods=['GET', 'POST'])
@login_required
def egitmen_yap(id):
    user = User.query.filter_by(id=id).first()
    user.role = 1
    new_egitmen = Egitmen(id = current_user.id)
    db.session.add(new_egitmen)
    db.session.commit()
    flash('Artık Eğitmensiniz, İlk kursunuzu yayınlamaya ne dersiniz!', category='success')
    return redirect('/yeni_kurs')

@views.route('/profil/<int:id>', methods=['GET', 'POST'])
@login_required
def profil(id):
    self_profil = 1
    user = User.query.get_or_404(id)
    kurslar = user.subscriptions
    result2 = db.engine.execute("SELECT DISTINCT kategori FROM Kurs")
    kategoriler = []
    for x in result2:
        a = str(x)
        end = len(a) - 3
        kategoriler.append(a[2:end])
    if user.id != current_user.id:
        self_profil = 0
    if user.role == 1:
        egitmen = Egitmen.query.filter_by(id=user.id).first()
        verilen_kurslar = db.engine.execute("SELECT Kurs.id,isim,kategori,first_name,last_name FROM Kurs, User WHERE Kurs.egitmen_id = User.id")
        return render_template("profil.html", self_profil = self_profil, user = user, egitmen = egitmen, verilen_kurslar = verilen_kurslar, kurslar = kurslar, kategoriler = kategoriler)

    return render_template("profil.html", self_profil = self_profil, user = user, kurslar = kurslar, kategoriler =kategoriler)

    
@views.route('/delete-note', methods=['POST'])
def delete_note():
    kurs = json.loads(request.data)
    noteId = kurs['noteId']
    kurs = Kurs.query.get(noteId)
    db.session.delete(kurs)
    db.session.commit()

    return jsonify({})