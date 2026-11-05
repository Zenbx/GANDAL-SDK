"""Client de la cellule IAM (decision-service + OIDC, contrat 1.7.0).

Sans endpoint configure, chaque methode leve CellUnavailable. Avec un endpoint,
les appels portent le Bearer du jeton (humain ou machine) et, sur les ecritures
qui le demandent, une Idempotency-Key (generee si absente).

Familles du contrat :
A OIDC/JWKS, B decisions, C sujets/roles/audit, D projets/acces,
E quotas/reservations, F machines/cles/STS/politiques, G ressources/tags.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from gandal_sdk._http import HttpTransport
from gandal_sdk.cells._base import not_ready
from gandal_sdk.cells.iam import models as m


def _idem(key: str | None = None) -> dict[str, str]:
    """En-tete Idempotency-Key obligatoire sur les mutations du contrat."""
    return {"Idempotency-Key": key or uuid.uuid4().hex}


def _corr(correlation_id: str | None) -> dict[str, str]:
    """En-tete de correlation optionnel X-Gandal-Correlation-Id."""
    if not correlation_id:
        return {}
    return {"X-Gandal-Correlation-Id": correlation_id}


def _hdr(
    *,
    idempotency_key: str | None = None,
    correlation_id: str | None = None,
    require_idem: bool = False,
) -> dict[str, str] | None:
    """Fusionne idempotence et correlation ; None si aucun en-tete."""
    headers: dict[str, str] = {}
    if require_idem or idempotency_key is not None:
        headers.update(_idem(idempotency_key))
    headers.update(_corr(correlation_id))
    return headers or None


def _params(**kwargs: Any) -> dict[str, Any] | None:
    """Query string sans cles a None."""
    cleaned = {k: v for k, v in kwargs.items() if v is not None}
    return cleaned or None


def _body(model: Any | None) -> Any | None:
    """Serialise un modele pydantic, un dict, ou None."""
    if model is None:
        return None
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json", exclude_none=True)
    return model


class IamCell:
    """Client de la cellule IAM (toutes les familles A-G du contrat)."""

    def __init__(self, transport: HttpTransport | None = None) -> None:
        """Sans transport (endpoint non configure), chaque appel leve CellUnavailable."""
        self._http = transport

    def _transport(self) -> HttpTransport:
        if self._http is None:
            not_ready("iam")
        return cast(HttpTransport, self._http)

    def _req(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self._transport().request(method, path, json=json, params=params, headers=headers)


    # --- A · OIDC / JWKS -------------------------------------------------------

    def openid_configuration(self) -> dict[str, Any]:
        """Document de discovery OIDC du fournisseur d'identite."""
        return self._req("GET", "/.well-known/openid-configuration")

    def jwks(self) -> dict[str, Any]:
        """Cles publiques JWKS pour verifier les jetons."""
        return self._req("GET", "/protocol/openid-connect/certs")

    # --- B · Decisions ---------------------------------------------------------

    def decide(
        self,
        demande: m.DemandeDecision | dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> m.Decision:
        """Demande une decision d'autorisation (POST /decisions)."""
        data = self._req(
            "POST",
            "/decisions",
            json=_body(demande),
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.Decision.model_validate(data)

    def decide_batch(
        self,
        demandes: list[m.DemandeDecision | dict[str, Any]],
        *,
        correlation_id: str | None = None,
    ) -> m.DecisionsGroupees:
        """Decisions groupees (POST /decisions:batch)."""
        payload = {
            "demandes": [
                d.model_dump(mode="json", exclude_none=True) if hasattr(d, "model_dump") else d
                for d in demandes
            ]
        }
        data = self._req(
            "POST",
            "/decisions:batch",
            json=payload,
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.DecisionsGroupees.model_validate(data)

    def list_actions(self, *, correlation_id: str | None = None) -> m.CatalogueActions:
        """Catalogue des actions connues du moteur de decision."""
        data = self._req("GET", "/actions", headers=_hdr(correlation_id=correlation_id))
        return m.CatalogueActions.model_validate(data)

    # --- C · Sujets, roles, audit ----------------------------------------------

    def list_subjects(
        self,
        *,
        curseur: str | None = None,
        taille: int | None = None,
        correlation_id: str | None = None,
    ) -> m.PageSujets:
        """Liste paginee des sujets."""
        data = self._req(
            "GET",
            "/subjects",
            params=_params(curseur=curseur, taille=taille),
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.PageSujets.model_validate(data)

    def create_subject(
        self,
        *,
        identifiant: str,
        courriel: str | None = None,
        prenom: str | None = None,
        nom: str | None = None,
        groupes: list[str] | None = None,
        externe: bool | None = None,
        expire_a: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Sujet:
        """Cree un sujet (compte)."""
        body = {
            k: v
            for k, v in {
                "identifiant": identifiant,
                "courriel": courriel,
                "prenom": prenom,
                "nom": nom,
                "groupes": groupes,
                "externe": externe,
                "expire_a": expire_a,
            }.items()
            if v is not None
        }
        data = self._req(
            "POST",
            "/subjects",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Sujet.model_validate(data)

    def get_me(self, *, correlation_id: str | None = None) -> m.Sujet:
        """Sujet correspondant au jeton courant."""
        data = self._req("GET", "/subjects/me", headers=_hdr(correlation_id=correlation_id))
        return m.Sujet.model_validate(data)

    def get_subject(self, subject_id: str, *, correlation_id: str | None = None) -> m.Sujet:
        """Lit un sujet par identifiant."""
        data = self._req(
            "GET",
            f"/subjects/{subject_id}",
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.Sujet.model_validate(data)

    def deactivate_subject(
        self,
        subject_id: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.DesactivationSujet:
        """Desactive un sujet (jamais d'effacement)."""
        data = self._req(
            "DELETE",
            f"/subjects/{subject_id}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.DesactivationSujet.model_validate(data)

    def patch_subject_attributes(
        self,
        subject_id: str,
        attributs: dict[str, str],
        *,
        motif: str | None = None,
        fin_a: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Sujet:
        """Ajuste les attributs (derogations) d'un sujet."""
        body = {"attributs": attributs}
        if motif is not None:
            body["motif"] = motif
        if fin_a is not None:
            body["fin_a"] = fin_a
        data = self._req(
            "PATCH",
            f"/subjects/{subject_id}/attributes",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Sujet.model_validate(data)

    def get_subject_quotas(
        self, subject_id: str, *, correlation_id: str | None = None
    ) -> m.Quotas:
        """Quotas d'un sujet."""
        data = self._req(
            "GET",
            f"/subjects/{subject_id}/quotas",
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.Quotas.model_validate(data)

    def get_subject_roles(
        self, subject_id: str, *, correlation_id: str | None = None
    ) -> m.RolesSujet:
        """Roles portes par un sujet."""
        data = self._req(
            "GET",
            f"/subjects/{subject_id}/roles",
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.RolesSujet.model_validate(data)

    def set_subject_roles(
        self,
        subject_id: str,
        roles: list[m.RoleAttribue | dict[str, Any]],
        *,
        motif: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Sujet:
        """Remplace les roles d'un sujet."""
        payload_roles = [
            r.model_dump(mode="json", exclude_none=True) if hasattr(r, "model_dump") else r
            for r in roles
        ]
        body: dict[str, Any] = {"roles": payload_roles}
        if motif is not None:
            body["motif"] = motif
        data = self._req(
            "PUT",
            f"/subjects/{subject_id}/roles",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Sujet.model_validate(data)

    def list_audit(
        self,
        *,
        curseur: str | None = None,
        taille: int | None = None,
        correlation_id: str | None = None,
    ) -> m.PageAudit:
        """Journal d'audit IAM."""
        data = self._req(
            "GET",
            "/audit",
            params=_params(curseur=curseur, taille=taille),
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.PageAudit.model_validate(data)

    # --- D · Projets et acces --------------------------------------------------

    def list_projects(
        self,
        *,
        curseur: str | None = None,
        taille: int | None = None,
        correlation_id: str | None = None,
    ) -> m.PageProjets:
        """Liste paginee des projets visibles."""
        data = self._req(
            "GET",
            "/projects",
            params=_params(curseur=curseur, taille=taille),
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.PageProjets.model_validate(data)

    def create_project(
        self,
        *,
        nom: str,
        description: str | None = None,
        environnement: m.Environnement | str | None = None,
        plan: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Projet:
        """Cree un projet."""
        body = {
            k: (v.value if isinstance(v, m.Environnement) else v)
            for k, v in {
                "nom": nom,
                "description": description,
                "environnement": environnement,
                "plan": plan,
            }.items()
            if v is not None
        }
        data = self._req(
            "POST",
            "/projects",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Projet.model_validate(data)

    def get_project(self, project_id: str, *, correlation_id: str | None = None) -> m.Projet:
        """Lit un projet."""
        data = self._req(
            "GET",
            f"/projects/{project_id}",
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.Projet.model_validate(data)

    def archive_project(
        self,
        project_id: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Projet:
        """Archive un projet."""
        data = self._req(
            "DELETE",
            f"/projects/{project_id}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Projet.model_validate(data)

    def list_members(
        self, project_id: str, *, correlation_id: str | None = None
    ) -> m.MembresProjet:
        """Membres d'un projet."""
        data = self._req(
            "GET",
            f"/projects/{project_id}/members",
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.MembresProjet.model_validate(data)

    def invite_member(
        self,
        project_id: str,
        *,
        sujet: str,
        capacite: m.Capacite | str,
        fin_a: str | None = None,
        motif: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Membre:
        """Invite un sujet existant dans un projet."""
        body: dict[str, Any] = {
            "sujet": sujet,
            "capacite": capacite.value if isinstance(capacite, m.Capacite) else capacite,
        }
        if fin_a is not None:
            body["fin_a"] = fin_a
        if motif is not None:
            body["motif"] = motif
        data = self._req(
            "POST",
            f"/projects/{project_id}/members",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Membre.model_validate(data)

    def remove_member(
        self,
        project_id: str,
        subject_id: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Retire un membre d'un projet."""
        self._req(
            "DELETE",
            f"/projects/{project_id}/members/{subject_id}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def change_member_capacity(
        self,
        project_id: str,
        subject_id: str,
        *,
        capacite: m.Capacite | str,
        fin_a: str | None = None,
        motif: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Membre:
        """Change la capacite d'un membre."""
        body: dict[str, Any] = {
            "capacite": capacite.value if isinstance(capacite, m.Capacite) else capacite,
        }
        if fin_a is not None:
            body["fin_a"] = fin_a
        if motif is not None:
            body["motif"] = motif
        data = self._req(
            "PATCH",
            f"/projects/{project_id}/members/{subject_id}",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Membre.model_validate(data)

    def create_member(
        self,
        project_id: str,
        membre: m.MembreNouveau | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Cree un compte et l'ajoute au projet en un appel."""
        return self._req(
            "POST",
            f"/projects/{project_id}/members:create",
            json=_body(membre),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def transfer_project(
        self,
        project_id: str,
        *,
        nouveau_proprietaire: str,
        motif: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Projet:
        """Transfere la propriete d'un projet."""
        body: dict[str, Any] = {"nouveau_proprietaire": nouveau_proprietaire}
        if motif is not None:
            body["motif"] = motif
        data = self._req(
            "POST",
            f"/projects/{project_id}/transfer",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Projet.model_validate(data)

    def list_access_requests(
        self, *, correlation_id: str | None = None
    ) -> m.PageDemandesAcces:
        """Liste les demandes d'acces."""
        data = self._req(
            "GET", "/access-requests", headers=_hdr(correlation_id=correlation_id)
        )
        return m.PageDemandesAcces.model_validate(data)

    def request_access(
        self,
        *,
        projet: str,
        capacite: m.Capacite | str,
        motif: str | None = None,
        fin_a: str | None = None,
        duree_s: int | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.DemandeAcces:
        """Demande l'acces a un projet."""
        body: dict[str, Any] = {
            "projet": projet,
            "capacite": capacite.value if isinstance(capacite, m.Capacite) else capacite,
        }
        for key, value in (("motif", motif), ("fin_a", fin_a), ("duree_s", duree_s)):
            if value is not None:
                body[key] = value
        data = self._req(
            "POST",
            "/access-requests",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.DemandeAcces.model_validate(data)

    def decide_access_request(
        self,
        request_id: str,
        *,
        verdict: str,
        capacite: m.Capacite | str | None = None,
        fin_a: str | None = None,
        motif: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.DemandeAcces:
        """Approuve ou refuse une demande d'acces."""
        body: dict[str, Any] = {"verdict": verdict}
        if capacite is not None:
            body["capacite"] = (
                capacite.value if isinstance(capacite, m.Capacite) else capacite
            )
        if fin_a is not None:
            body["fin_a"] = fin_a
        if motif is not None:
            body["motif"] = motif
        data = self._req(
            "POST",
            f"/access-requests/{request_id}/decide",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.DemandeAcces.model_validate(data)

    # --- E · Quotas ------------------------------------------------------------

    def get_my_quotas(self, *, correlation_id: str | None = None) -> m.Quotas:
        """Quotas de l'appelant."""
        data = self._req("GET", "/quotas", headers=_hdr(correlation_id=correlation_id))
        return m.Quotas.model_validate(data)

    def get_quota_aggregates(self, *, correlation_id: str | None = None) -> m.Agregats:
        """Agregats d'engagement de quotas (vue plateforme)."""
        data = self._req(
            "GET", "/quota-aggregates", headers=_hdr(correlation_id=correlation_id)
        )
        return m.Agregats.model_validate(data)

    def publish_quota_capacity(
        self,
        *,
        mesures: dict[str, Any] | list[Any],
        mesure_le: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.CapacitePubliee:
        """Publie la capacite physique mesuree par la plateforme."""
        body: dict[str, Any] = {"mesures": mesures}
        if mesure_le is not None:
            body["mesure_le"] = mesure_le
        data = self._req(
            "POST",
            "/quota-capacity",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.CapacitePubliee.model_validate(data)

    def list_quota_proposals(
        self, *, correlation_id: str | None = None
    ) -> m.PagePropositions:
        """Propositions de modification de plan."""
        data = self._req(
            "GET", "/quota-proposals", headers=_hdr(correlation_id=correlation_id)
        )
        return m.PagePropositions.model_validate(data)

    def propose_quota_plan(
        self,
        *,
        plan: str,
        changements: dict[str, int],
        justification: str,
        effet_a: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Proposition:
        """Propose une modification de plan de quotas."""
        body: dict[str, Any] = {
            "plan": plan,
            "changements": changements,
            "justification": justification,
        }
        if effet_a is not None:
            body["effet_a"] = effet_a
        data = self._req(
            "POST",
            "/quota-proposals",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Proposition.model_validate(data)

    def decide_quota_proposal(
        self,
        proposal_id: str,
        *,
        verdict: str,
        motif: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.DecisionProposition:
        """Decide sur une proposition de plan."""
        body: dict[str, Any] = {"verdict": verdict}
        if motif is not None:
            body["motif"] = motif
        data = self._req(
            "POST",
            f"/quota-proposals/{proposal_id}/decide",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.DecisionProposition.model_validate(data)

    def reserve_quota(
        self,
        *,
        ressources: dict[str, int],
        projet: str | None = None,
        duree_s: int | None = None,
        ressource_portee: str | None = None,
        sujet_delegue: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Reservation:
        """Reserve du quota avant creation de ressource."""
        body: dict[str, Any] = {"ressources": ressources}
        for key, value in (
            ("projet", projet),
            ("duree_s", duree_s),
            ("ressource_portee", ressource_portee),
            ("sujet_delegue", sujet_delegue),
        ):
            if value is not None:
                body[key] = value
        data = self._req(
            "POST",
            "/quota-reservations",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Reservation.model_validate(data)

    def get_reservation(
        self, reservation_id: str, *, correlation_id: str | None = None
    ) -> m.Reservation:
        """Lit une reservation de quota."""
        data = self._req(
            "GET",
            f"/quota-reservations/{reservation_id}",
            headers=_hdr(correlation_id=correlation_id),
        )
        return m.Reservation.model_validate(data)

    def release_reservation(
        self,
        reservation_id: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """Libere une reservation non confirmee."""
        self._req(
            "DELETE",
            f"/quota-reservations/{reservation_id}",
            headers=_hdr(correlation_id=correlation_id),
        )

    def commit_reservation(
        self,
        reservation_id: str,
        *,
        ressource_id: str,
        ressource_type: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Reservation:
        """Confirme une reservation apres creation effective."""
        body: dict[str, Any] = {"ressource_id": ressource_id}
        if ressource_type is not None:
            body["ressource_type"] = ressource_type
        data = self._req(
            "POST",
            f"/quota-reservations/{reservation_id}/commit",
            json=body,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Reservation.model_validate(data)

    def release_resource(
        self,
        resource_id: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Quotas:
        """Libere le quota d'une ressource detruite."""
        data = self._req(
            "POST",
            f"/resources/{resource_id}/release",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Quotas.model_validate(data)

    def resize_resource(
        self,
        resource_id: str,
        quantites: dict[str, int],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> m.Quotas:
        """Redimensionne une ressource comptee (POST /resources/{id}/resize).

        Les quantites sont ABSOLUES, pas un ecart : c'est IAM qui soustrait, dans
        sa transaction. Les cles absentes restent inchangees. Seules les
        ressources de `stock` se redimensionnent — une ressource de periode se
        consomme et rend 422.
        """
        data = self._req(
            "POST",
            f"/resources/{resource_id}/resize",
            json={"quantites": quantites},
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
        return m.Quotas.model_validate(data)

    # --- F · Machines, cles, STS, politiques -----------------------------------

    def create_machine_identity(
        self,
        machine: m.MachineEntree | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Cree une identite machine."""
        return self._req(
            "POST",
            "/machine-identities",
            json=_body(machine),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def list_access_keys(
        self, *, sujet: str | None = None, correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Liste les cles d'acces (sans secret)."""
        return self._req(
            "GET",
            "/access-keys",
            params=_params(sujet=sujet),
            headers=_hdr(correlation_id=correlation_id),
        )

    def create_access_key(
        self,
        cle: m.CleEntree | dict[str, Any] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Cree une cle ; le secret n'est rendu que dans cette reponse (sans Idempotency-Key)."""
        return self._req(
            "POST",
            "/access-keys",
            json=_body(cle) or {},
            headers=_hdr(correlation_id=correlation_id),
        )

    def delete_access_key(
        self,
        key_id: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Supprime une cle d'acces."""
        return self._req(
            "DELETE",
            f"/access-keys/{key_id}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def set_access_key_status(
        self,
        key_id: str,
        statut: m.CleStatut | m.CleStatutValeur | dict[str, Any] | str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Active ou desactive une cle."""
        if isinstance(statut, m.CleStatutValeur):
            payload: Any = {"statut": statut.value}
        elif isinstance(statut, str):
            payload = {"statut": statut}
        else:
            payload = _body(statut)
        return self._req(
            "PATCH",
            f"/access-keys/{key_id}",
            json=payload,
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def assume_role(
        self,
        demande: m.DemandeAssomption | dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Endosse un role et recoit des identifiants temporaires (sans Idempotency-Key)."""
        return self._req(
            "POST",
            "/sts/assume-role",
            json=_body(demande),
            headers=_hdr(correlation_id=correlation_id),
        )

    def revoke_session(
        self,
        session_id: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Revoque une session STS."""
        return self._req(
            "DELETE",
            f"/sts/sessions/{session_id}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def whoami(self, *, correlation_id: str | None = None) -> dict[str, Any]:
        """Identite effective de la session courante (STS)."""
        return self._req("GET", "/sts/whoami", headers=_hdr(correlation_id=correlation_id))

    def list_assumable_roles(self, *, correlation_id: str | None = None) -> dict[str, Any]:
        """Roles assumables."""
        return self._req(
            "GET", "/assumable-roles", headers=_hdr(correlation_id=correlation_id)
        )

    def create_assumable_role(
        self,
        role: m.RoleEntree | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Cree un role assumable."""
        return self._req(
            "POST",
            "/assumable-roles",
            json=_body(role),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def get_assumable_role(
        self, name: str, *, correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Lit un role assumable."""
        return self._req(
            "GET",
            f"/assumable-roles/{name}",
            headers=_hdr(correlation_id=correlation_id),
        )

    def delete_assumable_role(
        self,
        name: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Supprime un role assumable."""
        return self._req(
            "DELETE",
            f"/assumable-roles/{name}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def attach_policy_to_role(
        self,
        role_name: str,
        policy_name: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Attache une politique a un role assumable."""
        return self._req(
            "PUT",
            f"/assumable-roles/{role_name}/policies/{policy_name}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def detach_policy_from_role(
        self,
        role_name: str,
        policy_name: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Detache une politique d'un role assumable."""
        return self._req(
            "DELETE",
            f"/assumable-roles/{role_name}/policies/{policy_name}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def revoke_role_sessions(
        self,
        role_name: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Revoque toutes les sessions d'un role."""
        return self._req(
            "POST",
            f"/assumable-roles/{role_name}/revoke-sessions",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def list_policies(self, *, correlation_id: str | None = None) -> dict[str, Any]:
        """Liste les politiques."""
        return self._req("GET", "/policies", headers=_hdr(correlation_id=correlation_id))

    def create_policy(
        self,
        politique: m.PolitiqueEntree | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Cree une politique."""
        return self._req(
            "POST",
            "/policies",
            json=_body(politique),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def get_policy(self, name: str, *, correlation_id: str | None = None) -> dict[str, Any]:
        """Lit une politique."""
        return self._req(
            "GET", f"/policies/{name}", headers=_hdr(correlation_id=correlation_id)
        )

    def delete_policy(
        self,
        name: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Supprime une politique."""
        return self._req(
            "DELETE",
            f"/policies/{name}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def attach_policy(
        self,
        name: str,
        attachement: m.AttachementEntree | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Attache une politique a une cible."""
        return self._req(
            "POST",
            f"/policies/{name}/attachments",
            json=_body(attachement),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def detach_policy_organisation(
        self,
        name: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Detache une politique de l'organisation."""
        return self._req(
            "DELETE",
            f"/policies/{name}/attachments/organisation",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def detach_policy(
        self,
        name: str,
        cible_type: str,
        cible: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Detache une politique d'une cible."""
        return self._req(
            "DELETE",
            f"/policies/{name}/attachments/{cible_type}/{cible}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def generate_base_policies(
        self,
        demande: m.DemandeEngendrer | dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Engendre les politiques de base."""
        return self._req(
            "POST",
            "/policies:generate",
            json=_body(demande) or {},
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def simulate_policies(
        self,
        demande: m.DemandeSimulation | dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Simule l'evaluation de politiques sans effet de bord."""
        return self._req(
            "POST",
            "/policies:simulate",
            json=_body(demande),
            headers=_hdr(correlation_id=correlation_id),
        )

    def list_policy_context_keys(
        self, *, correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Cles de contexte utilisables dans les politiques."""
        return self._req(
            "GET", "/policy-context-keys", headers=_hdr(correlation_id=correlation_id)
        )

    # --- G · Ressources et tags ------------------------------------------------

    def get_resource(
        self, resource_id: str, *, correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Lit les metadonnees IAM d'une ressource."""
        return self._req(
            "GET",
            f"/resources/{resource_id}",
            headers=_hdr(correlation_id=correlation_id),
        )

    def grant_resource_right(
        self,
        resource_id: str,
        droit: m.DroitEntree | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Accorde un droit sur une ressource."""
        return self._req(
            "POST",
            f"/resources/{resource_id}/grants",
            json=_body(droit),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def revoke_resource_right(
        self,
        resource_id: str,
        cible_type: str,
        cible: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Retire un droit sur une ressource."""
        return self._req(
            "DELETE",
            f"/resources/{resource_id}/grants/{cible_type}/{cible}",
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )

    def get_resource_quotas(
        self, resource_id: str, *, correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Quotas attaches a une ressource."""
        return self._req(
            "GET",
            f"/resources/{resource_id}/quotas",
            headers=_hdr(correlation_id=correlation_id),
        )

    def get_tags(
        self, portee: str, cible: str, *, correlation_id: str | None = None
    ) -> dict[str, Any]:
        """Lit les attributs (tags) d'une cible."""
        return self._req(
            "GET",
            f"/tags/{portee}/{cible}",
            headers=_hdr(correlation_id=correlation_id),
        )

    def set_tags(
        self,
        portee: str,
        cible: str,
        attributs: m.AttributsEntree | dict[str, Any],
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Pose les attributs (tags) d'une cible."""
        return self._req(
            "PATCH",
            f"/tags/{portee}/{cible}",
            json=_body(attributs),
            headers=_hdr(
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                require_idem=True,
            ),
        )
