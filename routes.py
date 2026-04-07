import os
from flask import Flask, render_template, request, redirect, session, jsonify
from sqlalchemy import inspect, text
from models import db, Taxi, Reservation, User, Correspondent, FixedRoute

app = Flask(__name__)
app.secret_key = 'secret123'  # باش نخزنوا session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taxi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

db.init_app(app)


def _ensure_correspondent_sonnerie_column():
    """SQLite : create_all() n'ajoute pas les colonnes aux tables existantes."""
    insp = inspect(db.engine)
    if 'correspondent' not in insp.get_table_names():
        return
    cols = {c['name'] for c in insp.get_columns('correspondent')}
    if 'sonnerie' not in cols:
        db.session.execute(
            text("ALTER TABLE correspondent ADD COLUMN sonnerie VARCHAR(32) DEFAULT 'classic'")
        )
        db.session.commit()


def _ensure_table_column(table: str, column: str, ddl: str):
    insp = inspect(db.engine)
    if table not in insp.get_table_names():
        return
    cols = {c['name'] for c in insp.get_columns(table)}
    if column not in cols:
        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
        db.session.commit()


def _ensure_schema_upgrades():
    # Taxi
    _ensure_table_column('taxi', 'places_total', "places_total INTEGER NOT NULL DEFAULT 6")
    _ensure_table_column('taxi', 'status', "status VARCHAR(20) NOT NULL DEFAULT 'en_attente'")
    _ensure_table_column('taxi', 'queue_num', "queue_num INTEGER")
    _ensure_table_column('taxi', 'chauffeur_id', "chauffeur_id INTEGER")
    _ensure_table_column('taxi', 'current_lat', "current_lat FLOAT")
    _ensure_table_column('taxi', 'current_lng', "current_lng FLOAT")
    _ensure_table_column('taxi', 'permis_confiance_path', "permis_confiance_path VARCHAR(255)")
    _ensure_table_column('taxi', 'autorisation_sortie_path', "autorisation_sortie_path VARCHAR(255)")
    _ensure_table_column('taxi', 'agrement_verifie', "agrement_verifie BOOLEAN NOT NULL DEFAULT 0")
    _ensure_table_column('taxi', 'created_at', "created_at DATETIME")

    # Reservation
    _ensure_table_column('reservation', 'seats', "seats INTEGER NOT NULL DEFAULT 1")
    _ensure_table_column('reservation', 'payment_method', "payment_method VARCHAR(20) NOT NULL DEFAULT 'cash'")
    _ensure_table_column('reservation', 'created_at', "created_at DATETIME")


def _seed_fixed_routes_if_empty():
    if FixedRoute.query.count() > 0:
        return
    seeds = [
        ("Casablanca", "Settat", 25.0),
        ("Casablanca", "Rabat", 40.0),
        ("Rabat", "Fes", 70.0),
        ("Casablanca", "Marrakech", 90.0),
    ]
    for d, a, p in seeds:
        db.session.add(FixedRoute(ville_depart=d, ville_arrivee=a, prix_par_siege=p, actif=True))
    db.session.commit()


with app.app_context():
    db.create_all()
    _ensure_correspondent_sonnerie_column()
    _ensure_schema_upgrades()
    _seed_fixed_routes_if_empty()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helpers auth/roles
def _require_login():
    return 'user_id' in session


def _require_role(role: str):
    return session.get('role') == role


def _current_user_id():
    return session.get('user_id')


def _sanitize_filename(name: str) -> str:
    # keep it simple (Windows-safe-ish)
    keep = []
    for ch in (name or ""):
        if ch.isalnum() or ch in ('.', '-', '_'):
            keep.append(ch)
        elif ch in (' ',):
            keep.append('_')
    out = ''.join(keep).strip('._')
    return out or "file"


def _get_official_price_per_seat(ville_depart: str, ville_arrivee: str):
    route = FixedRoute.query.filter_by(ville_depart=ville_depart, ville_arrivee=ville_arrivee, actif=True).first()
    if route:
        return float(route.prix_par_siege)
    # fallback (quand la route n'est pas renseignée)
    return None


def _estimate_price(ville_depart: str, ville_arrivee: str, seats: int):
    p = _get_official_price_per_seat(ville_depart, ville_arrivee)
    if p is None:
        return None
    return round(p * max(1, int(seats)), 2)


# الصفحة الرئيسية
@app.route('/')
def index():
    # page d'accueil = interface passager (liste simple)
    taxis = Taxi.query.order_by(Taxi.created_at.desc()).all()
    return render_template('index.html', taxis=taxis)


@app.route('/passager', methods=['GET'])
def passager():
    ville_depart = (request.args.get('ville_depart') or '').strip()
    ville_arrivee = (request.args.get('ville_arrivee') or '').strip()
    q = Taxi.query
    if ville_depart:
        q = q.filter(Taxi.ville_depart == ville_depart)
    if ville_arrivee:
        q = q.filter(Taxi.ville_arrivee == ville_arrivee)
    taxis = q.order_by(Taxi.created_at.desc()).all()
    return render_template('passager.html', taxis=taxis, ville_depart=ville_depart, ville_arrivee=ville_arrivee)


@app.route('/chauffeur', methods=['GET', 'POST'])
def chauffeur():
    if not _require_login() or not _require_role('chauffeur'):
        return redirect('/login')
    uid = _current_user_id()
    if request.method == 'POST':
        action = request.form.get('action') or ''
        if action == 'pointer':
            # prend le prochain numéro de file
            max_q = db.session.execute(text("SELECT COALESCE(MAX(queue_num), 0) FROM taxi")).scalar() or 0
            ville_depart = (request.form.get('ville_depart') or '').strip()
            ville_arrivee = (request.form.get('ville_arrivee') or '').strip()
            if ville_depart and ville_arrivee:
                taxi = Taxi(
                    ville_depart=ville_depart,
                    ville_arrivee=ville_arrivee,
                    places=6,
                    places_total=6,
                    queue_num=int(max_q) + 1,
                    chauffeur_id=uid,
                    status="en_attente",
                )
                db.session.add(taxi)
                db.session.commit()
        elif action == 'upload_docs':
            taxi_id = request.form.get('taxi_id', type=int)
            taxi = Taxi.query.get(taxi_id)
            if taxi and taxi.chauffeur_id == uid:
                permis = request.files.get('permis_confiance')
                autor = request.files.get('autorisation_sortie')
                if permis and permis.filename:
                    fn = _sanitize_filename(permis.filename)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], f"permis_{uid}_{taxi.id}_{fn}")
                    permis.save(path)
                    taxi.permis_confiance_path = os.path.relpath(path, app.root_path).replace("\\", "/")
                if autor and autor.filename:
                    fn = _sanitize_filename(autor.filename)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], f"autor_{uid}_{taxi.id}_{fn}")
                    autor.save(path)
                    taxi.autorisation_sortie_path = os.path.relpath(path, app.root_path).replace("\\", "/")
                db.session.commit()
        elif action == 'maj_position':
            taxi_id = request.form.get('taxi_id', type=int)
            lat = request.form.get('lat', type=float)
            lng = request.form.get('lng', type=float)
            taxi = Taxi.query.get(taxi_id)
            if taxi and taxi.chauffeur_id == uid:
                taxi.current_lat = lat
                taxi.current_lng = lng
                taxi.status = request.form.get('status') or taxi.status
                db.session.commit()
        return redirect('/chauffeur')
    my_taxis = Taxi.query.filter_by(chauffeur_id=uid).order_by(Taxi.created_at.desc()).all()
    return render_template('chauffeur.html', taxis=my_taxis)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not _require_login() or not _require_role('admin'):
        return redirect('/login')
    if request.method == 'POST':
        action = request.form.get('action') or ''
        if action == 'toggle_agrement':
            taxi_id = request.form.get('taxi_id', type=int)
            taxi = Taxi.query.get(taxi_id)
            if taxi:
                taxi.agrement_verifie = not bool(taxi.agrement_verifie)
                db.session.commit()
        elif action == 'add_route':
            d = (request.form.get('ville_depart') or '').strip()
            a = (request.form.get('ville_arrivee') or '').strip()
            p = request.form.get('prix_par_siege', type=float)
            if d and a and p is not None and p > 0:
                db.session.add(FixedRoute(ville_depart=d, ville_arrivee=a, prix_par_siege=float(p), actif=True))
                db.session.commit()
        elif action == 'toggle_route':
            rid = request.form.get('route_id', type=int)
            r = FixedRoute.query.get(rid)
            if r:
                r.actif = not bool(r.actif)
                db.session.commit()
        return redirect('/admin')
    taxis = Taxi.query.order_by(Taxi.created_at.desc()).all()
    routes = FixedRoute.query.order_by(FixedRoute.ville_depart.asc(), FixedRoute.ville_arrivee.asc()).all()
    return render_template('admin.html', taxis=taxis, routes=routes)

# إضافة طاكسي (خاص بالسائق)
@app.route('/ajouter_taxi', methods=['POST'])
def ajouter_taxi():
    if 'role' not in session or session['role'] != 'chauffeur':
        taxis = Taxi.query.all()
        return render_template('index.html', taxis=taxis, error="Accès refusé. Connectez-vous en tant que chauffeur.")
    ville_depart = request.form['ville_depart']
    ville_arrivee = request.form['ville_arrivee']
    # dans Taxi GO : on remplit 6 sièges
    taxi = Taxi(ville_depart=ville_depart, ville_arrivee=ville_arrivee, places=6, places_total=6, chauffeur_id=_current_user_id())
    db.session.add(taxi)
    db.session.commit()
    return redirect('/')

# الحجز (خاص بالزبون)
@app.route('/reserver/<int:taxi_id>', methods=['GET', 'POST'])
def reserver(taxi_id):
    taxi = Taxi.query.get_or_404(taxi_id)
    if request.method == 'POST':
        nom_client = request.form['nom_client']
        seats = request.form.get('seats', type=int) or 1
        payment_method = (request.form.get('payment_method') or 'cash').strip()
        if payment_method not in ('cash', 'wallet'):
            payment_method = 'cash'
        seats = max(1, min(int(seats), 6))
        if taxi.places >= seats:
            taxi.places -= seats
            reservation = Reservation(nom_client=nom_client, taxi_id=taxi.id, seats=seats, payment_method=payment_method)
            db.session.add(reservation)
            db.session.commit()
            return redirect('/passager')
        else:
            return render_template('reserver.html', taxi=taxi, error="Plus de places disponibles.")
    # estimation prix (si route officielle existe)
    est = _estimate_price(taxi.ville_depart, taxi.ville_arrivee, 1)
    return render_template('reserver.html', taxi=taxi, estimation=est)


@app.route('/api/taxi/<int:taxi_id>/status')
def api_taxi_status(taxi_id):
    taxi = Taxi.query.get_or_404(taxi_id)
    occupees = max(0, int(taxi.places_total or 6) - int(taxi.places or 0))
    return jsonify({
        "id": taxi.id,
        "ville_depart": taxi.ville_depart,
        "ville_arrivee": taxi.ville_arrivee,
        "places_total": int(taxi.places_total or 6),
        "places_dispo": int(taxi.places or 0),
        "places_occupees": occupees,
        "status": taxi.status,
        "lat": taxi.current_lat,
        "lng": taxi.current_lng,
        "agrement_verifie": bool(taxi.agrement_verifie),
        "queue_num": taxi.queue_num,
    })

# تسجيل جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form['nom']
        role = request.form['role']
        if role not in ('client', 'chauffeur', 'admin'):
            role = 'client'
        user = User(nom=nom, role=role)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['role'] = user.role
        if role == 'chauffeur':
            return redirect('/chauffeur')
        if role == 'admin':
            return redirect('/admin')
        return redirect('/passager')
    return render_template('register.html')

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nom = request.form['nom']
        user = User.query.filter_by(nom=nom).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'chauffeur':
                return redirect('/chauffeur')
            if user.role == 'admin':
                return redirect('/admin')
            return redirect('/passager')
        else:
            return render_template('login.html', error="Utilisateur introuvable / المستخدم ما موجود")
    return render_template('login.html')

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


SONNERIES_VALIDES = frozenset({'classic', 'bell', 'digital', 'soft', 'urgent', 'melody'})


@app.route('/correspondants', methods=['GET', 'POST'])
def correspondants():
    if 'user_id' not in session:
        return redirect('/login')
    uid = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            nom = (request.form.get('nom') or '').strip()
            sonnerie = (request.form.get('sonnerie') or 'classic').strip()
            if nom and sonnerie in SONNERIES_VALIDES:
                db.session.add(Correspondent(user_id=uid, nom=nom, sonnerie=sonnerie))
                db.session.commit()
        elif action == 'edit':
            cid = request.form.get('correspondent_id', type=int)
            nom = (request.form.get('nom') or '').strip()
            sonnerie = (request.form.get('sonnerie') or 'classic').strip()
            c = Correspondent.query.get(cid)
            if c and c.user_id == uid and nom and sonnerie in SONNERIES_VALIDES:
                c.nom = nom
                c.sonnerie = sonnerie
                db.session.commit()
        elif action == 'delete':
            cid = request.form.get('correspondent_id', type=int)
            c = Correspondent.query.get(cid)
            if c and c.user_id == uid:
                db.session.delete(c)
                db.session.commit()
        return redirect('/correspondants')
    items = Correspondent.query.filter_by(user_id=uid).order_by(Correspondent.nom).all()
    return render_template('correspondants.html', correspondants=items)


if __name__ == "__main__":
    app.run(debug=True)


