"""
Dokumentladen — Unterstützt PDF, DOCX, TXT, MD
Extrahiert Text und Metadaten aus Verwaltungsdokumenten.
"""

import os
from datetime import datetime
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None


class DocumentLoader:
    """Lädt Dokumente aus verschiedenen Formaten und extrahiert Text samt Metadaten."""

    UNTERSTÜTZTE_FORMATE = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self, upload_verzeichnis: str = "uploads"):
        self.upload_verzeichnis = upload_verzeichnis
        os.makedirs(upload_verzeichnis, exist_ok=True)

    def lade_dokument(
        self,
        dateipfad: str,
        titel: Optional[str] = None,
        abteilung: Optional[str] = None,
        version: Optional[str] = None,
    ) -> dict:
        """Lädt ein Dokument und gibt Text mit Metadaten zurück."""
        if not os.path.exists(dateipfad):
            raise FileNotFoundError(f"Datei nicht gefunden: {dateipfad}")

        endung = os.path.splitext(dateipfad)[1].lower()
        if endung not in self.UNTERSTÜTZTE_FORMATE:
            raise ValueError(
                f"Format '{endung}' nicht unterstützt. "
                f"Erlaubt: {', '.join(self.UNTERSTÜTZTE_FORMATE)}"
            )

        try:
            if endung == ".pdf":
                text = self._lade_pdf(dateipfad)
            elif endung == ".docx":
                text = self._lade_docx(dateipfad)
            elif endung in (".txt", ".md"):
                text = self._lade_text(dateipfad)
            else:
                raise ValueError(f"Unbekanntes Format: {endung}")
        except Exception as e:
            raise RuntimeError(f"Fehler beim Laden von '{dateipfad}': {e}") from e

        if not text.strip():
            raise ValueError(f"Dokument '{dateipfad}' enthält keinen extrahierbaren Text.")

        metadaten = {
            "titel": titel or os.path.splitext(os.path.basename(dateipfad))[0],
            "dateiname": os.path.basename(dateipfad),
            "abteilung": abteilung or "Unbekannt",
            "version": version or "1.0",
            "hochladedatum": datetime.now().isoformat(),
            "format": endung[1:].upper(),
            "zeichenanzahl": len(text),
        }

        return {"text": text, "metadaten": metadaten}

    def _lade_pdf(self, dateipfad: str) -> str:
        """Extrahiert Text aus einer PDF-Datei."""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 ist erforderlich für PDF-Unterstützung. Installieren mit: pip install PyPDF2")

        text_seiten = []
        with open(dateipfad, "rb") as f:
            leser = PyPDF2.PdfReader(f)
            for seite in leser.pages:
                seiten_text = seite.extract_text()
                if seiten_text:
                    text_seiten.append(seiten_text)

        return "\n\n".join(text_seiten)

    def _lade_docx(self, dateipfad: str) -> str:
        """Extrahiert Text aus einer DOCX-Datei."""
        if Document is None:
            raise ImportError("python-docx ist erforderlich für DOCX-Unterstützung. Installieren mit: pip install python-docx")

        doc = Document(dateipfad)
        absätze = []
        for absatz in doc.paragraphs:
            if absatz.text.strip():
                absätze.append(absatz.text)

        return "\n\n".join(absätze)

    def _lade_text(self, dateipfad: str) -> str:
        """Lädt eine reine Text- oder Markdown-Datei."""
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                with open(dateipfad, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise RuntimeError(f"Datei '{dateipfad}' konnte mit keinem unterstützten Encoding gelesen werden.")

    def prüfe_datei(self, dateipfad: str) -> dict:
        """Prüft eine Datei auf Integrität und unterstütztes Format."""
        ergebnis = {
            "dateipfad": dateipfad,
            "existiert": os.path.exists(dateipfad),
            "format": os.path.splitext(dateipfad)[1].lower(),
            "unterstützt": False,
            "größe_kb": 0,
            "fehler": None,
        }

        if ergebnis["existiert"]:
            ergebnis["größe_kb"] = round(os.path.getsize(dateipfad) / 1024, 1)
            ergebnis["unterstützt"] = ergebnis["format"] in self.UNTERSTÜTZTE_FORMATE

        return ergebnis
