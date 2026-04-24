"""
Antwortengine — Generiert Antworten mit Ollama (lokal)
Nutzt RAG-Kontext und liefert Quellenangaben.
"""

import os
import requests
from typing import Optional


class AnswerEngine:
    """Generiert KI-Antworten basierend auf Vektor-Suche und Ollama."""

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        modell_name: Optional[str] = None,
    ):
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.modell_name = modell_name or os.getenv("MODEL_NAME", "llama3")
        self.system_prompt = self._lade_prompt("prompts/rag_answer.txt")
        self.rewrite_prompt = self._lade_prompt("prompts/query_rewrite.txt")

    def _lade_prompt(self, pfad: str) -> str:
        """Lädt einen System-Prompt aus einer Datei."""
        if os.path.exists(pfad):
            with open(pfad, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def ermittle_kontext(self, treffer: list) -> str:
        """Formattiert Suchtreffer als Kontext für die KI."""
        if not treffer:
            return "Es wurden keine relevanten Dokumente gefunden."

        kontext_teile = []
        for i, t in enumerate(treffer, 1):
            quelle = t["metadaten"].get("dateiname", "Unbekannt")
            titel = t["metadaten"].get("titel", "")
            abschnitt = t["text"]
            kontext_teile.append(
                f"[Quelle {i}] {titel} ({quelle})\n{abschnitt}"
            )

        return "\n\n---\n\n".join(kontext_teile)

    def generiere_antwort(
        self,
        frage: str,
        treffer: list,
        rolle: str = "sachbearbeitung",
    ) -> dict:
        """Generiert eine Antwort auf Basis der Suchtreffer."""
        kontext = self.ermittle_kontext(treffer)
        konfidenz = self._bewerte_konfidenz(treffer)

        prüfung = self._guardrail_prüfung(frage, treffer)
        if prüfung["blockiert"]:
            return {
                "antwort": prüfung["grund"],
                "quellen": [],
                "konfidenz": 0.0,
                "warnung": prüfung["grund"],
            }

        if not treffer or konfidenz < 0.15:
            return {
                "antwort": "Dazu liegen keine ausreichenden Informationen vor. "
                "Bitte wenden Sie sich an eine Fachkraft oder erweitern Sie die Suchanfrage.",
                "quellen": [],
                "konfidenz": konfidenz,
                "warnung": "Keine ausreichenden Quellen gefunden.",
            }

        prompt = f"{self.system_prompt}\n\n---\n\nKontext:\n{kontext}\n\n---\n\nFrage: {frage}"

        try:
            antwort = self._ollama_anfrage(prompt)
        except Exception as e:
            antwort = f"Fehler bei der KI-Anfrage: {e}"
            konfidenz = 0.0

        quellen = [
            {
                "dateiname": t["metadaten"].get("dateiname", "Unbekannt"),
                "titel": t["metadaten"].get("titel", ""),
                "relevanz": t["relevanz"],
            }
            for t in treffer
        ]

        warnung = None
        if konfidenz < 0.4:
            warnung = "⚠️ Niedrige Konfidenz — bitte prüfen Sie die Quellen."

        return {
            "antwort": antwort,
            "quellen": quellen,
            "konfidenz": konfidenz,
            "warnung": warnung,
        }

    def _ollama_anfrage(self, prompt: str) -> str:
        """Sendet eine Anfrage an Ollama (lokal)."""
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.modell_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 1024,
            },
        }

        antwort = requests.post(url, json=payload, timeout=120)
        antwort.raise_for_status()
        daten = antwort.json()
        return daten.get("response", "").strip()

    def _bewerte_konfidenz(self, treffer: list) -> float:
        """Bewertet die Konfidenz basierend auf den Suchtreffern."""
        if not treffer:
            return 0.0

        relevanzen = [t["relevanz"] for t in treffer]
        durchschnitt = sum(relevanzen) / len(relevanzen)

        # Bonus für mehrere gute Treffer
        gute_treffer = sum(1 for r in relevanzen if r > 0.6)
        bonus = min(gute_treffer * 0.05, 0.15)

        return min(durchschnitt + bonus, 1.0)

    def _guardrail_prüfung(self, frage: str, treffer: list) -> dict:
        """Prüft, ob die Anfrage beantwortet werden darf."""
        # Kategorien, die nicht automatisch beantwortet werden
        blockierte_themen = [
            "rechtsberatung", "rechtsverbindlich", "verbindliche auskunft",
            "gerichtsverfahren", "straftat", "anzeige erstatten",
        ]

        frage_klein = frage.lower()
        for thema in blockierte_themen:
            if thema in frage_klein:
                return {
                    "blockiert": True,
                    "grund": (
                        "Diese Anfrage erfordert eine verbindliche rechtliche Prüfung "
                        "und kann nicht automatisch beantwortet werden. "
                        "Bitte wenden Sie sich an die Rechtsabteilung."
                    ),
                }

        return {"blockiert": False}

    def formuliere_anfrage_um(self, frage: str) -> str:
        """Formuliert eine Anfrage für eine bessere Vektorsuche um."""
        prompt = f"{self.rewrite_prompt}\n\nUrsprüngliche Anfrage: {frage}"

        try:
            ergebnis = self._ollama_anfrage(prompt)
            return ergebnis.strip() if ergebnis else frage
        except Exception:
            return frage
