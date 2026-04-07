# fichier: grande_taxi_maroc.py

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Ville:
    id: int
    nom: str


@dataclass
class Taxi:
    id: int
    numero: str
    nb_places: int
    ville_depart_id: int  # ville de base


@dataclass
class Trajet:
    id: int
    ville_depart_id: int
    ville_arrivee_id: int
    prix_par_place: float
    taxi_id: int


@dataclass
class Reservation:
    id: int
    trajet_id: int
    nom_client: str
    nb_places: int


class SystemeGrandeTaxi:
    def __init__(self):
        self.villes: List[Ville] = []
        self.taxis: List[Taxi] = []
        self.trajets: List[Trajet] = []
        self.reservations: List[Reservation] = []

        self._next_ville_id = 1
        self._next_taxi_id = 1
        self._next_trajet_id = 1
        self._next_resa_id = 1

    # ---------------- VILLES ----------------
    def ajouter_ville(self, nom: str) -> Ville:
        ville = Ville(id=self._next_ville_id, nom=nom)
        self.villes.append(ville)
        self._next_ville_id += 1
        return ville

    def lister_villes(self):
        if not self.villes:
            print("Aucune ville enregistrée.")
            return
        for v in self.villes:
            print(f"{v.id}. {v.nom}")

    def trouver_ville(self, ville_id: int) -> Optional[Ville]:
        for v in self.villes:
            if v.id == ville_id:
                return v
        return None

    # ---------------- TAXIS ----------------
    def ajouter_taxi(self, numero: str, nb_places: int, ville_depart_id: int) -> Taxi:
        taxi = Taxi(
            id=self._next_taxi_id,
            numero=numero,
            nb_places=nb_places,
            ville_depart_id=ville_depart_id,
        )
        self.taxis.append(taxi)
        self._next_taxi_id += 1
        return taxi

    def lister_taxis(self):
        if not self.taxis:
            print("Aucun taxi enregistré.")
            return
        for t in self.taxis:
            ville = self.trouver_ville(t.ville_depart_id)
            nom_ville = ville.nom if ville else "Inconnue"
            print(
                f"{t.id}. Taxi {t.numero} - {t.nb_places} places - Ville de base: {nom_ville}"
            )

    def trouver_taxi(self, taxi_id: int) -> Optional[Taxi]:
        for t in self.taxis:
            if t.id == taxi_id:
                return t
        return None

    # ---------------- TRAJETS ----------------
    def ajouter_trajet(
        self,
        ville_depart_id: int,
        ville_arrivee_id: int,
        prix_par_place: float,
        taxi_id: int,
    ) -> Trajet:
        trajet = Trajet(
            id=self._next_trajet_id,
            ville_depart_id=ville_depart_id,
            ville_arrivee_id=ville_arrivee_id,
            prix_par_place=prix_par_place,
            taxi_id=taxi_id,
        )
        self.trajets.append(trajet)
        self._next_trajet_id += 1
        return trajet

    def lister_trajets(self):
        if not self.trajets:
            print("Aucun trajet enregistré.")
            return
        for tr in self.trajets:
            vd = self.trouver_ville(tr.ville_depart_id)
            va = self.trouver_ville(tr.ville_arrivee_id)
            taxi = self.trouver_taxi(tr.taxi_id)
            nom_vd = vd.nom if vd else "Inconnue"
            nom_va = va.nom if va else "Inconnue"
            num_taxi = taxi.numero if taxi else "Inconnu"
            places_dispo = self.places_disponibles(tr.id)
            print(
                f"{tr.id}. {nom_vd} -> {nom_va} | Taxi {num_taxi} | "
                f"Prix/place: {tr.prix_par_place} MAD | Places dispo: {places_dispo}"
            )

    def trouver_trajet(self, trajet_id: int) -> Optional[Trajet]:
        for tr in self.trajets:
            if tr.id == trajet_id:
                return tr
        return None

    # ---------------- RESERVATIONS ----------------
    def places_reservees(self, trajet_id: int) -> int:
        total = 0
        for r in self.reservations:
            if r.trajet_id == trajet_id:
                total += r.nb_places
        return total

    def places_disponibles(self, trajet_id: int) -> int:
        trajet = self.trouver_trajet(trajet_id)
        if not trajet:
            return 0
        taxi = self.trouver_taxi(trajet.taxi_id)
        if not taxi:
            return 0
        return taxi.nb_places - self.places_reservees(trajet_id)

    def ajouter_reservation(
        self, trajet_id: int, nom_client: str, nb_places: int
    ) -> Optional[Reservation]:
        dispo = self.places_disponibles(trajet_id)
        if nb_places > dispo:
            print(
                f"Impossible de réserver {nb_places} place(s). "
                f"Places disponibles: {dispo}."
            )
            return None

        resa = Reservation(
            id=self._next_resa_id,
            trajet_id=trajet_id,
            nom_client=nom_client,
            nb_places=nb_places,
        )
        self.reservations.append(resa)
        self._next_resa_id += 1
        return resa

    def lister_reservations(self):
        if not self.reservations:
            print("Aucune réservation enregistrée.")
            return
        for r in self.reservations:
            trajet = self.trouver_trajet(r.trajet_id)
            if trajet:
                vd = self.trouver_ville(trajet.ville_depart_id)
                va = self.trouver_ville(trajet.ville_arrivee_id)
                nom_vd = vd.nom if vd else "Inconnue"
                nom_va = va.nom if va else "Inconnue"
                print(
                    f"{r.id}. {r.nom_client} - {r.nb_places} place(s) "
                    f"sur trajet {nom_vd} -> {nom_va}"
                )


def afficher_menu():
    print("\n=== Gestion des grands taxis (Maroc) ===")
    print("1. Ajouter une ville")
    print("2. Lister les villes")
    print("3. Ajouter un taxi")
    print("4. Lister les taxis")
    print("5. Ajouter un trajet")
    print("6. Lister les trajets")
    print("7. Ajouter une réservation")
    print("8. Lister les réservations")
    print("0. Quitter")


def main():
    systeme = SystemeGrandeTaxi()

    # Quelques données de base (exemple)
    systeme.ajouter_ville("Casablanca")
    systeme.ajouter_ville("Rabat")
    systeme.ajouter_ville("Marrakech")
    systeme.ajouter_ville("Fès")

    while True:
        afficher_menu()
        choix = input("Votre choix: ").strip()

        if choix == "1":
            nom = input("Nom de la ville: ").strip()
            ville = systeme.ajouter_ville(nom)
            print(f"Ville ajoutée avec ID {ville.id}.")
        elif choix == "2":
            systeme.lister_villes()
        elif choix == "3":
            numero = input("Numéro du taxi (ex: 12345-أ-1): ").strip()
            try:
                nb_places = int(input("Nombre de places: "))
            except ValueError:
                print("Nombre de places invalide.")
                continue

            print("Ville de base (ID) :")
            systeme.lister_villes()
            try:
                ville_id = int(input("ID de la ville: "))
            except ValueError:
                print("ID invalide.")
                continue

            if not systeme.trouver_ville(ville_id):
                print("Ville introuvable.")
                continue

            taxi = systeme.ajouter_taxi(numero, nb_places, ville_id)
            print(f"Taxi ajouté avec ID {taxi.id}.")
        elif choix == "4":
            systeme.lister_taxis()
        elif choix == "5":
            print("Ville de départ (ID):")
            systeme.lister_villes()
            try:
                vd_id = int(input("ID ville départ: "))
            except ValueError:
                print("ID invalide.")
                continue

            print("Ville d'arrivée (ID):")
            systeme.lister_villes()
            try:
                va_id = int(input("ID ville arrivée: "))
            except ValueError:
                print("ID invalide.")
                continue

            if not systeme.trouver_ville(vd_id) or not systeme.trouver_ville(va_id):
                print("Ville départ ou arrivée introuvable.")
                continue

            print("Choisir un taxi (ID):")
            systeme.lister_taxis()
            try:
                taxi_id = int(input("ID du taxi: "))
            except ValueError:
                print("ID invalide.")
                continue

            if not systeme.trouver_taxi(taxi_id):
                print("Taxi introuvable.")
                continue

            try:
                prix = float(input("Prix par place (MAD): "))
            except ValueError:
                print("Prix invalide.")
                continue

            trajet = systeme.ajouter_trajet(vd_id, va_id, prix, taxi_id)
            print(f"Trajet ajouté avec ID {trajet.id}.")
        elif choix == "6":
            systeme.lister_trajets()
        elif choix == "7":
            systeme.lister_trajets()
            try:
                trajet_id = int(input("ID du trajet: "))
            except ValueError:
                print("ID invalide.")
                continue

            if not systeme.trouver_trajet(trajet_id):
                print("Trajet introuvable.")
                continue

            nom_client = input("Nom du client: ").strip()
            try:
                nb_places = int(input("Nombre de places à réserver: "))
            except ValueError:
                print("Nombre invalide.")
                continue

            resa = systeme.ajouter_reservation(trajet_id, nom_client, nb_places)
            if resa:
                print(
                    f"Réservation ajoutée avec ID {resa.id}. "
                    f"Total places réservées sur ce trajet: "
                    f"{systeme.places_reservees(trajet_id)}"
                )
        elif choix == "8":
            systeme.lister_reservations()
        elif choix == "0":
            print("Au revoir.")
            break
        else:
            print("Choix invalide, réessayez.")


if __name__ == "__main__":
    main()