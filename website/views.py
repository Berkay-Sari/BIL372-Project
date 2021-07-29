from flask import Blueprint, render_template, request, flash, jsonify, redirect
from flask_login import login_required, current_user
from .models import Kurs, User
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        kurs = request.form.get('kurs')
        new_kurs = Kurs(kategori=kurs)
        db.session.add(new_kurs)
        new_kurs.subscribers.append(current_user)
        db.session.commit()
        flash('Kurs eklendi!', category='success')

    result = db.engine.execute("SELECT * FROM Kurs")
    return render_template("home.html", user=current_user, kurslar= result)

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
    return render_template("kurs_profil.html", user=current_user, kurs = kurs)

@views.route('/hesap_ayarları', methods=['GET', 'POST'])
def update_hesap_ayar():
    return render_template("hesap_ayarları.html", user = current_user)
    #Eski Hali
    #current_user.role = 1;
    #db.session.commit()
    #flash('Artık eğitmensiniz!', category='success')
    #return redirect('/')
    
@views.route('/profil_ayarları', methods=['GET', 'POST'])
def update_profil():
    return render_template("profil_ayarları.html", user = current_user)

@views.route('/foto_ayarları', methods=['GET', 'POST'])
def update_foto():
    return render_template("foto_ayarları.html", user = current_user)


@views.route('/profil/<int:id>', methods=['GET', 'POST'])
@login_required
def profil(id):
    self_profil = 1
    user = User.query.get_or_404(id)
    if user.id != current_user.id:
        self_profil = 0
    
    return render_template("profil.html", self_profil = self_profil, user = user)
            

# @views.route('/egitmen_profil/<int:id>', methods=['GET', 'POST'])
# @login_required
# def profil(id):
#     user = User.query.get_or_404(id)
#     return render_template("egitmen_profil.html", egitmen=user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    kurs = json.loads(request.data)
    noteId = kurs['noteId']
    kurs = Kurs.query.get(noteId)
    db.session.delete(kurs)
    db.session.commit()

    return jsonify({})
