"""
TextChunker — Intelligentes Zerlegen von Verwaltungstexten
Respektiert Überschriften und behält Kontext bei.
"""

import re
from typing import List


class TextChunker:
    """Zerlegt Text in handhabbare Abschnitte unter Beachtung von Überschriften."""

    def __init__(self, chunk_größe: int = 500, überlappung: int = 100):
        """
        Args:
            chunk_größe: Maximale Zeichenanzahl pro Abschnitt
            überlappung: Zeichenanzahl der Überlappung zwischen Abschnitten
        """
        if überlappung >= chunk_größe:
            raise ValueError("Überlappung muss kleiner als Chunk-Größe sein.")
        self.chunk_größe = chunk_größe
        self.überlappung = überlappung

    def zerlege_text(self, text: str, metadaten: dict = None) -> List[dict]:
        """Zerlegt einen Text in Abschnitte mit Metadaten."""
        text = self._bereinige_text(text)
        abschnitte = self._aufteilung_nach_ueberschriften(text)
        chunks = []

        for idx, abschnitt in enumerate(abschnitte):
            if len(abschnitt) <= self.chunk_größe:
                chunks.append(self._erstelle_chunk(abschnitt, idx, metadaten))
            else:
                sub_chunks = self._zerlege_großen_abschnitt(abschnitt, metadaten, idx)
                chunks.extend(sub_chunks)

        return chunks

    def _bereinige_text(self, text: str) -> str:
        """Bereinigt Text: entferne übermäßige Leerzeichen, Seitenzahlen, etc."""
        # Mehrfache Leerzeichen reduzieren
        text = re.sub(r" {3,}", " ", text)
        # Mehrfache Leerzeilen reduzieren
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        # Trailing whitespace entfernen
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip()

    def _aufteilung_nach_ueberschriften(self, text: str) -> List[str]:
        """Teilt Text anhand von Überschriften auf."""
        # Überschriftenmuster: # Markdown, 1. / 1.1 nummeriert, GROSSBUCHSTABEN
        überschrift_muster = re.compile(
            r"^(#{1,6}\s+.+|"
            r"\d+(?:\.\d+)*\s+[A-ZÄÖÜ][^\n]+|"
            r"[A-ZÄÖÜ][A-ZÄÖÜ\s]{5,})$",
            re.MULTILINE,
        )

        positionen = [0]
        for treffer in überschrift_muster.finditer(text):
            if treffer.start() > 0:
                positionen.append(treffer.start())

        abschnitte = []
        for i in range(len(positionen)):
            start = positionen[i]
            ende = positionen[i + 1] if i + 1 < len(positionen) else len(text)
            abschnitt = text[start:ende].strip()
            if abschnitt:
                abschnitte.append(abschnitt)

        return abschnitte if abschnitte else [text]

    def _zerlege_großen_abschnitt(
        self, text: str, metadaten: dict, basis_idx: int
    ) -> List[dict]:
        """Zerlegt einen zu großen Abschnitt unter Beibehaltung der Überlappung."""
        chunks = []
        schritt = self.chunk_größe - self.überlappung
        position = 0
        sub_idx = 0

        while position < len(text):
            ende = min(position + self.chunk_größe, len(text))
            stück = text[position:ende]
            chunks.append(self._erstelle_chunk(stück, basis_idx * 100 + sub_idx, metadaten))
            position += schritt
            sub_idx += 1

            if ende >= len(text):
                break

        return chunks

    def _erstelle_chunk(self, text: str, idx: int, metadaten: dict = None) -> dict:
        """Erstellt ein Chunk-Objekt mit Metadaten."""
        chunk_metadaten = {"chunk_index": idx}
        if metadaten:
            chunk_metadaten.update(metadaten)

        # Erste Zeile als mögliche Überschrift erkennen
        zeilen = text.split("\n")
        überschrift = ""
        for zeile in zeilen:
            if zeile.strip() and len(zeile.strip()) < 100:
                überschrift = zeile.strip()
                break

        return {
            "text": text.strip(),
            "metadaten": chunk_metadaten,
            "überschrift": überschrift,
            "zeichenanzahl": len(text.strip()),
        }

    def erhalte_ueberschrift(self, text: str) -> str:
        """Extrahiert die wahrscheinlichste Überschrift aus einem Textabschnitt."""
        zeilen = text.strip().split("\n")
        for zeile in zeilen:
            geputzt = zeile.strip()
            if geputzt and len(geputzt) < 100 and not geputzt.endswith("."):
                return geputzt
        return ""
