"""
Berechtigungsmodell — Rollen und Dokumentzugriff
Einfaches RBAC für kommunale Verwaltung.
"""

from typing import List, Optional


# Verfügbare Rollen
ROLLEN = ["sachbearbeitung", "teamleitung", "admin"]

# Verfügbare Vertraulichkeitsstufen
STUFEN = ["oeffentlich", "intern", "fachbereich", "vertraulich"]

# Berechtigungsmatrix: Rolle -> erlaubte Stufen
BERECHTIGUNGEN = {
    "sachbearbeitung": ["oeffentlich", "intern"],
    "teamleitung": ["oeffentlich", "intern", "fachbereich"],
    "admin": ["oeffentlich", "intern", "fachbereich", "vertraulich"],
}


class PermissionManager:
    """Verwaltet Rollen und Dokumentzugriffsberechtigungen."""

    def __init__(self):
        self._aktive_rolle = "sachbearbeitung"

    def setze_rolle(self, rolle: str) -> bool:
        """Setzt die aktive Rolle für die aktuelle Sitzung."""
        if rolle not in ROLLEN:
            return False
        self._aktive_rolle = rolle
        return True

    def ermittle_rolle(self) -> str:
        """Gibt die aktuell aktive Rolle zurück."""
        return self._aktive_rolle

    def prüfe_zugriff(self, stufe: str, rolle: Optional[str] = None) -> bool:
        """Prüft, ob eine Rolle auf eine bestimmte Vertraulichkeitsstufe zugreifen darf."""
        rolle = rolle or self._aktive_rolle
        erlaubt = BERECHTIGUNGEN.get(rolle, [])
        return stufe in erlaubt

    def filtere_dokumente(
        self, dokumente: List[dict], rolle: Optional[str] = None
    ) -> List[dict]:
        """Filtert eine Liste von Dokumenten nach den Berechtigungen der Rolle."""
        rolle = rolle or self._aktive_rolle
        erlaubt = set(BERECHTIGUNGEN.get(rolle, []))
        return [
            doc for doc in dokumente
            if doc.get("tags", ["oeffentlich"])[0] in erlaubt
            or any(tag in erlaubt for tag in doc.get("tags", []))
        ]

    def filtere_treffer(self, treffer: List[dict], rolle: Optional[str] = None) -> List[dict]:
        """Filtert Vektor-Suchtreffer nach Berechtigungen."""
        rolle = rolle or self._aktive_rolle
        erlaubt = set(BERECHTIGUNGEN.get(rolle, []))
        return [
            t for t in treffer
            if t.get("metadaten", {}).get("tags", ["oeffentlich"])[0] in erlaubt
        ]

    def gib_erlaubte_stufen(self, rolle: Optional[str] = None) -> List[str]:
        """Gibt die erlaubten Vertraulichkeitsstufen für eine Rolle zurück."""
        rolle = rolle or self._aktive_rolle
        return list(BERECHTIGUNGEN.get(rolle, []))

    def gib_alle_rollen(self) -> List[str]:
        """Gibt alle verfügbaren Rollen zurück."""
        return list(ROLLEN)

    def gib_berechtigungsmatrix(self) -> dict:
        """Gibt die vollständige Berechtigungsmatrix zurück."""
        return dict(BERECHTIGUNGEN)
