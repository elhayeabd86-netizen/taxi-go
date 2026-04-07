from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    # petite helper locale (évite une dépendance externe)
    import datetime as _dt
    return _dt.datetime.utcnow()


class Taxi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ville_depart = db.Column(db.String(50), nullable=False)
    ville_arrivee = db.Column(db.String(50), nullable=False)
    # "places" = places restantes (réservation par siège, sur 6 par défaut)
    places = db.Column(db.Integer, nullable=False)
    places_total = db.Column(db.Integer, nullable=False, default=6)
    status = db.Column(db.String(20), nullable=False, default="en_attente")  # en_attente | en_route | termine
    queue_num = db.Column(db.Integer, nullable=True)  # pointage à la station (Mahatta)
    chauffeur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    permis_confiance_path = db.Column(db.String(255), nullable=True)
    autorisation_sortie_path = db.Column(db.String(255), nullable=True)
    agrement_verifie = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_client = db.Column(db.String(50), nullable=False)
    taxi_id = db.Column(db.Integer, db.ForeignKey('taxi.id'), nullable=False)
    seats = db.Column(db.Integer, nullable=False, default=1)
    payment_method = db.Column(db.String(20), nullable=False, default="cash")  # cash | wallet
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # client | chauffeur | admin


class Correspondent(db.Model):
    """Contact avec une sonnerie personnalisée (clé utilisée côté client pour Web Audio)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nom = db.Column(db.String(80), nullable=False)
    sonnerie = db.Column(db.String(32), nullable=False, default='classic')


class FixedRoute(db.Model):
    """Routes fixes + tarif officiel par siège (géré côté admin)."""
    id = db.Column(db.Integer, primary_key=True)
    ville_depart = db.Column(db.String(50), nullable=False)
    ville_arrivee = db.Column(db.String(50), nullable=False)
    prix_par_siege = db.Column(db.Float, nullable=False)
    actif = db.Column(db.Boolean, nullable=False, default=True)
