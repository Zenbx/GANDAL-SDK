"""Modeles de la cellule IAM (contrat openapi/gandal-iam.json, familles A-G)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Capacite(StrEnum):
    """Position dans un projet (pas un role de compte)."""

    PROPRIETAIRE = "proprietaire"
    CONTRIBUTEUR = "contributeur"
    LECTEUR = "lecteur"


class DecisionVerdict(StrEnum):
    """Verdict d'une decision d'autorisation."""

    PERMIT = "permit"
    DENY = "deny"


class DecisionMotif(StrEnum):
    """Code stable du motif de decision (enumeration fermee du contrat)."""

    PROPRIETAIRE = "proprietaire"
    CAPACITE_PROJET = "capacite_projet"
    ROLE = "role"
    ACCES_CONCEDE = "acces_concede"
    QUOTA_DEPASSE = "quota_depasse"
    CONTEXTE_MANQUANT = "contexte_manquant"
    UNKNOWN_ACTION = "unknown_action"
    SECOND_FACTEUR_REQUIS = "second_facteur_requis"
    COMPTE_REVOQUE = "compte_revoque"
    ROLE_EXPIRE = "role_expire"
    AUTO_ATTRIBUTION = "auto_attribution"
    ELEVATION_INTERDITE = "elevation_interdite"
    REFUS_PAR_DEFAUT = "refus_par_defaut"
    POLITIQUE = "politique"
    POLITIQUE_PORTE_PASSANTE = "politique_porte_passante"
    POLITIQUE_REFUS_EXPLICITE = "politique_refus_explicite"
    POLITIQUE_HORS_FRONTIERE = "politique_hors_frontiere"
    POLITIQUE_HORS_ORGANISATION = "politique_hors_organisation"
    POLITIQUE_HORS_SESSION = "politique_hors_session"
    POLITIQUE_ILLISIBLE = "politique_illisible"


class ObligationType(StrEnum):
    """Obligation que l'appelant doit honorer sur un permit."""

    JOURNALISER = "journaliser"
    NOTIFIER = "notifier"
    EXPIRER_A = "expirer_a"
    RESERVER_QUOTA = "reserver_quota"


class RoleNom(StrEnum):
    """Les deux roles de compte du contrat."""

    USER = "user"
    ADMIN = "admin"


class ProjetEtat(StrEnum):
    """Etat d'un projet IAM."""

    ACTIF = "actif"
    ARCHIVE = "archive"


class Environnement(StrEnum):
    """Environnement d'un projet."""

    DEVELOPPEMENT = "developpement"
    PRODUCTION = "production"


class DemandeAccesEtat(StrEnum):
    """Etat d'une demande d'acces a un projet."""

    EN_ATTENTE = "en_attente"
    APPROUVEE = "approuvee"
    REFUSEE = "refusee"
    EXPIREE = "expiree"


class NatureQuota(StrEnum):
    """Nature d'une ligne de quota."""

    STOCK = "stock"
    PERIODE = "periode"


class PorteeQuota(StrEnum):
    """Portee d'un ensemble de quotas."""

    COMPTE = "compte"
    PROJET = "projet"


class PropositionEtat(StrEnum):
    """Etat d'une proposition de plan."""

    EN_ATTENTE = "en_attente"
    APPLIQUEE = "appliquee"
    REFUSEE = "refusee"


class ReservationEtat(StrEnum):
    """Etat d'une reservation de quota."""

    RESERVEE = "reservee"
    CONFIRMEE = "confirmee"
    LIBEREE = "liberee"
    EXPIREE = "expiree"


class AuditResultat(StrEnum):
    """Resultat d'une ligne d'audit."""

    PERMIT = "permit"
    DENY = "deny"
    SUCCES = "succes"
    ECHEC = "echec"


class CleStatutValeur(StrEnum):
    """Statut d'une cle d'acces machine."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class GenrePolitique(StrEnum):
    """Genre d'un document de politique."""

    IDENTITE = "identite"
    RESSOURCE = "ressource"
    FRONTIERE = "frontiere"
    SESSION = "session"
    ORGANISATION = "organisation"


class CibleAttachement(StrEnum):
    """Type de cible pour attacher une politique."""

    SUJET = "sujet"
    ROLE = "role"
    PROJET = "projet"
    ORGANISATION = "organisation"


class CibleDroit(StrEnum):
    """Type de cible pour un droit sur une ressource."""

    SUJET = "sujet"
    GROUPE = "groupe"
    ATTRIBUT = "attribut"


class Obligation(BaseModel):
    """Action obligatoire si l'appelant applique un permit."""

    type: ObligationType
    valeur: str | None = None


class DemandeRessource(BaseModel):
    """Ressource visee par une demande de decision."""

    type: str
    id: str | None = None
    projet: str | None = None
    proprietaire: str | None = None


class DemandeDecision(BaseModel):
    """Corps de POST /decisions."""

    action: str
    ressource: DemandeRessource
    contexte: dict[str, Any] | None = None
    sujet_delegue: str | None = None


class Decision(BaseModel):
    """Reponse d'une decision d'autorisation."""

    decision: DecisionVerdict
    motif: DecisionMotif
    valide_jusqu_a: datetime
    correlation_id: str
    explication: str | None = None
    regle: str | None = None
    obligations: list[Obligation] = Field(default_factory=list)


class RoleAttribue(BaseModel):
    """Role porte par un sujet, avec fenetre de validite."""

    nom: RoleNom
    debut_a: datetime | None = None
    fin_a: datetime | None = None
    accorde_par: str | None = None
    accorde_le: datetime | None = None


class Sujet(BaseModel):
    """Compte (humain ou machine) connu d'IAM."""

    id: str
    roles: list[RoleAttribue]
    attributs: dict[str, str]
    correlation_id: str
    identifiant: str | None = None
    courriel: str | None = None
    actif: bool = True
    externe: bool = False
    expire_a: datetime | None = None
    groupes: list[str] = Field(default_factory=list)


class Membre(BaseModel):
    """Membre d'un projet avec sa capacite."""

    sujet: str
    capacite: Capacite
    identifiant: str | None = None
    fin_a: datetime | None = None
    invite_par: str | None = None
    invite_le: datetime | None = None


class LigneQuota(BaseModel):
    """Une limite de quota et sa consommation."""

    ressource: str
    nature: NatureQuota
    limite: int
    consomme: int
    reserve: int
    restant: int
    remise_a_zero_a: datetime | None = None


class Quotas(BaseModel):
    """Quotas d'un compte ou d'un projet."""

    portee: PorteeQuota
    limites: list[LigneQuota]
    correlation_id: str
    sujet: str | None = None
    projet: str | None = None
    plan: str | None = None
    derogation_jusqu_a: datetime | None = None


class Projet(BaseModel):
    """Projet IAM : portee des capacites et des quotas."""

    id: str
    nom: str
    proprietaire: str
    etat: ProjetEtat
    description: str | None = None
    environnement: Environnement | None = None
    plan: str | None = None
    membres: list[Membre] = Field(default_factory=list)
    quotas: Quotas | None = None
    cree_le: datetime | None = None
    correlation_id: str | None = None


class DemandeAcces(BaseModel):
    """Demande d'acces a un projet en attente de decision."""

    id: str
    projet: str
    demandeur: str
    capacite: Capacite
    etat: DemandeAccesEtat
    fin_a: datetime | None = None
    motif: str | None = None
    decide_par: str | None = None
    decide_le: datetime | None = None
    motif_decision: str | None = None
    expire_a: datetime | None = None
    correlation_id: str | None = None


class LigneAgregat(BaseModel):
    """Engagement et consommation agreges pour une ressource."""

    ressource: str
    nature: NatureQuota
    engage: int
    consomme: int
    reserve: int | None = None
    disponible: int | None = None
    ratio_engagement: float | None = None
    sujets: int | None = None


class Agregats(BaseModel):
    """Vue plateforme des quotas engages."""

    lignes: list[LigneAgregat]
    correlation_id: str
    plan: str | None = None
    mesure_le: datetime | None = None


class Proposition(BaseModel):
    """Proposition de modification d'un plan de quotas."""

    id: str
    plan: str
    changements: dict[str, int]
    justification: str
    etat: PropositionEtat
    limites_actuelles: dict[str, int] | None = None
    auteur: str | None = None
    decide_par: str | None = None
    decide_le: datetime | None = None
    effet_a: datetime | None = None
    correlation_id: str | None = None


class Reservation(BaseModel):
    """Reservation de quota avant creation effective d'une ressource."""

    id: str
    sujet: str
    etat: ReservationEtat
    expire_a: datetime
    ressources: dict[str, int]
    correlation_id: str
    projet: str | None = None
    ressource_id: str | None = None


class EvenementAudit(BaseModel):
    """Ligne du journal d'audit IAM."""

    horodatage: datetime
    auteur: str
    action: str
    resultat: AuditResultat
    correlation_id: str
    adresse_appelant: str | None = None
    ressource: str | None = None
    projet: str | None = None
    motif: str | None = None


class Action(BaseModel):
    """Action connue du catalogue de decisions."""

    nom: str
    cellule: str
    roles: list[RoleNom]
    capacites: list[Capacite] = Field(default_factory=list)
    second_facteur: bool = False
    description: str | None = None


class AttributsEntree(BaseModel):
    """Corps pour poser des attributs (tags)."""

    attributs: dict[str, str]
    motif: str | None = None


class DroitCapacite(StrEnum):
    """Capacite accordable sur une ressource (jamais proprietaire)."""

    CONTRIBUTEUR = "contributeur"
    LECTEUR = "lecteur"


class DroitEntree(BaseModel):
    """Corps pour accorder un droit sur une ressource."""

    cible_type: CibleDroit
    cible: str
    capacite: DroitCapacite
    fin_a: datetime | None = None
    motif: str | None = None


class MembreNouveau(BaseModel):
    """Creation d'un sujet et invitation dans un projet en un appel."""

    identifiant: str
    courriel: str
    capacite: Capacite = Capacite.CONTRIBUTEUR
    fin_a: datetime | None = None
    externe: bool = False
    expire_a: datetime | None = None
    motif: str | None = None


class PolitiqueEntree(BaseModel):
    """Creation ou remplacement d'une politique."""

    nom: str
    document: dict[str, Any]
    genre: GenrePolitique = GenrePolitique.IDENTITE
    description: str | None = None


class AttachementEntree(BaseModel):
    """Attachement d'une politique a une cible."""

    cible_type: CibleAttachement
    cible: str | None = None


class DemandeSimulation(BaseModel):
    """Simulation d'evaluation de politiques sans effet de bord."""

    action: str
    ressource: dict[str, Any] | None = None
    contexte: dict[str, Any] | None = None
    sujet_delegue: str | None = None


class DemandeEngendrer(BaseModel):
    """Demande de generation des politiques de base."""

    essai: bool = False


class MachineEntree(BaseModel):
    """Creation d'une identite machine."""

    nom: str
    description: str | None = None


class CleEntree(BaseModel):
    """Creation d'une cle d'acces (le secret n'est rendu qu'a la creation)."""

    sujet: str | None = None
    description: str | None = None


class CleStatut(BaseModel):
    """Changement de statut d'une cle."""

    statut: CleStatutValeur


class RoleEntree(BaseModel):
    """Definition d'un role assumable."""

    nom: str
    confiance: dict[str, Any]
    frontiere: str | None = None
    duree_max_s: int = 3600
    description: str | None = None


class DemandeAssomption(BaseModel):
    """Demande d'endossement de role (STS)."""

    role: str
    nom_session: str
    duree_s: int | None = None
    politique_session: dict[str, Any] | None = None
    id_externe: str | None = None


class PageSujets(BaseModel):
    """Page de sujets."""

    elements: list[Sujet]
    correlation_id: str
    curseur_suivant: str | None = None


class PageProjets(BaseModel):
    """Page de projets."""

    elements: list[Projet]
    correlation_id: str | None = None
    curseur_suivant: str | None = None


class PageAudit(BaseModel):
    """Page du journal d'audit."""

    elements: list[EvenementAudit]
    correlation_id: str | None = None
    curseur_suivant: str | None = None


class PageDemandesAcces(BaseModel):
    """Page de demandes d'acces."""

    elements: list[DemandeAcces]
    correlation_id: str | None = None


class PagePropositions(BaseModel):
    """Page de propositions de plan."""

    elements: list[Proposition]
    correlation_id: str | None = None


class CatalogueActions(BaseModel):
    """Catalogue des actions connues du PDP."""

    actions: list[Action]
    correlation_id: str | None = None


class DecisionsGroupees(BaseModel):
    """Reponse de POST /decisions:batch."""

    decisions: list[Decision]
    correlation_id: str | None = None


class DesactivationSujet(BaseModel):
    """Reponse a la desactivation d'un sujet."""

    sujet: Sujet
    correlation_id: str | None = None
    projets_a_reattribuer: list[str] = Field(default_factory=list)


class RolesSujet(BaseModel):
    """Roles lus pour un sujet."""

    roles: list[RoleAttribue]
    correlation_id: str | None = None


class MembresProjet(BaseModel):
    """Liste des membres d'un projet."""

    membres: list[Membre]
    correlation_id: str | None = None


class DecisionProposition(BaseModel):
    """Reponse a la decision sur une proposition de plan."""

    proposition: Proposition
    correlation_id: str | None = None
    sujets_au_dessus_de_la_limite: list[str] = Field(default_factory=list)


class CapacitePubliee(BaseModel):
    """Accuse de reception de POST /quota-capacity."""

    mesures: dict[str, Any] | list[Any] | None = None
    mesure_le: datetime | None = None
    correlation_id: str | None = None
