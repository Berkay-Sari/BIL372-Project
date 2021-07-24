from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Kurs
from . import db
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        kurs = request.form.get('kurs')
        new_kurs = Kurs(kategori=kurs) #user_id=current_user.id)
        db.session.add(new_kurs)
        #db.session.commit()
        new_kurs.subscribers.append(current_user)
        db.session.commit()
        flash('Kurs eklendi!', category='success')

    result = db.engine.execute("SELECT * FROM Kurs")
    return render_template("home.html", user=current_user, kurslar= result)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    kurs = json.loads(request.data)
    noteId = kurs['noteId']
    kurs = Kurs.query.get(noteId)
    db.session.delete(kurs)
    db.session.commit()

    return jsonify({})
