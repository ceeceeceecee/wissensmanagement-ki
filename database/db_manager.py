"""
Datenbank-Manager — CRUD-Operationen für Dokumente, Tags, Protokoll und Feedback
"""

import os
from datetime import datetime
from typing import List, Optional


class DatabaseManager:
    """Verwaltet alle Datenbankoperationen für das Wissensmanagement-System."""

    def __init__(self, datenbank_url: Optional[str] = None):
        self.datenbank_url = datenbank_url or os.getenv(
            "POSTGRES_URL", "postgresql://wissens:wissens@localhost:5432/wissensmanagement"
        )
        self._verbindung = None

    def _verbinde(self):
        """Stellt eine Datenbankverbindung her."""
        if self._verbindung is not None:
            return self._verbindung

        try:
            import psycopg2
            self._verbindung = psycopg2.connect(self.datenbank_url)
            self._verbindung.autocommit = False
            return self._verbindung
        except ImportError:
            raise ImportError(
                "psycopg2 ist erforderlich. Installieren mit: pip install psycopg2-binary"
            )
        except Exception as e:
            raise RuntimeError(f"Datenbankverbindung fehlgeschlagen: {e}") from e

    def schließe(self):
        """Schließt die Datenbankverbindung."""
        if self._verbindung is not None:
            self._verbindung.close()
            self._verbindung = None

    def initialisiere_db(self):
        """Lädt das Schema und erstellt alle Tabellen."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()

        schema_pfad = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_pfad, "r", encoding="utf-8") as f:
            sql = f.read()

        cursor.execute(sql)
        verbindung.commit()
        cursor.close()

    # --- Dokumente ---

    def dokument_hinzufuegen(self, titel: str, dateiname: str, abteilung: str = "Unbekannt",
                              version: str = "1.0", format_: str = "TXT",
                              zeichenanzahl: int = 0) -> int:
        """Fügt ein neues Dokument hinzu und gibt die ID zurück."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            """INSERT INTO dokumente (titel, dateiname, abteilung, version, format, zeichenanzahl)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (titel, dateiname, abteilung, version, format_, zeichenanzahl),
        )
        doc_id = cursor.fetchone()[0]
        verbindung.commit()
        cursor.close()
        return doc_id

    def dokument_laden(self, dokument_id: int) -> Optional[dict]:
        """Lädt ein Dokument anhand der ID."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute("SELECT * FROM dokumente WHERE id = %s", (dokument_id,))
        zeile = cursor.fetchone()
        cursor.close()

        if not zeile:
            return None

        spalten = ["id", "titel", "dateiname", "abteilung", "version", "format",
                    "zeichenanzahl", "hochladedatum", "status", "dateipfad"]
        return dict(zip(spalten, zeile))

    def alle_dokumente(self) -> List[dict]:
        """Gibt alle Dokumente zurück."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute("SELECT * FROM dokumente ORDER BY hochladedatum DESC")
        zeilen = cursor.fetchall()
        cursor.close()

        spalten = ["id", "titel", "dateiname", "abteilung", "version", "format",
                    "zeichenanzahl", "hochladedatum", "status", "dateipfad"]
        return [dict(zip(spalten, zeile)) for zeile in zeilen]

    def dokument_löschen(self, dokument_id: int) -> bool:
        """Löscht ein Dokument (soft delete)."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute("UPDATE dokumente SET status = 'gelöscht' WHERE id = %s", (dokument_id,))
        verbindung.commit()
        cursor.close()
        return cursor.rowcount > 0

    # --- Tags ---

    def tag_hinzufuegen(self, dokument_id: int, tag: str):
        """Fügt einen Tag zu einem Dokument hinzu."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            "INSERT INTO tags (dokument_id, tag) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (dokument_id, tag),
        )
        verbindung.commit()
        cursor.close()

    def tags_laden(self, dokument_id: int) -> List[str]:
        """Lädt alle Tags eines Dokuments."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute("SELECT tag FROM tags WHERE dokument_id = %s", (dokument_id,))
        tags = [zeile[0] for zeile in cursor.fetchall()]
        cursor.close()
        return tags

    # --- Anfrage-Protokoll ---

    def anfrage_protokollieren(self, frage: str, antwort: str, benutzer: str = "anonym",
                                rolle: str = "sachbearbeitung", quellenanzahl: int = 0,
                                konfidenz: float = 0.0, dauer_ms: int = 0) -> int:
        """Protokolliert eine Anfrage und gibt die ID zurück."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            """INSERT INTO anfrage_protokoll (frage, antwort, benutzer, rolle, quellenanzahl, konfidenz, verarbeitungszeit_ms)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (frage, antwort, benutzer, rolle, quellenanzahl, konfidenz, dauer_ms),
        )
        anfrage_id = cursor.fetchone()[0]
        verbindung.commit()
        cursor.close()
        return anfrage_id

    def häufige_anfragen(self, limit: int = 10) -> List[dict]:
        """Gibt die häufigsten Anfragen zurück."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            """SELECT frage, COUNT(*) as anzahl, AVG(konfidenz) as durchschnitt
               FROM anfrage_protokoll GROUP BY frage ORDER BY anzahl DESC LIMIT %s""",
            (limit,),
        )
        zeilen = cursor.fetchall()
        cursor.close()
        return [{"frage": z[0], "anzahl": z[1], "konfidenz": float(z[2] or 0)} for z in zeilen]

    def unbeantwortete_anfragen(self, limit: int = 10) -> List[dict]:
        """Gibt Anfragen mit niedriger Konfidenz zurück."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            """SELECT frage, konfidenz, erstellt_am FROM anfrage_protokoll
               WHERE konfidenz < 0.3 ORDER BY erstellt_am DESC LIMIT %s""",
            (limit,),
        )
        zeilen = cursor.fetchall()
        cursor.close()
        return [{"frage": z[0], "konfidenz": float(z[1]), "datum": z[2]} for z in zeilen]

    # --- Feedback ---

    def feedback_speichern(self, anfrage_id: int, bewertung: str, kommentar: str = ""):
        """Speichert Feedback zu einer Anfrage."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            "INSERT INTO feedback (anfrage_id, bewertung, kommentar) VALUES (%s, %s, %s)",
            (anfrage_id, bewertung, kommentar),
        )
        verbindung.commit()
        cursor.close()

    def feedback_statistik(self) -> dict:
        """Gibt eine Zusammenfassung des Feedbacks zurück."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()
        cursor.execute(
            """SELECT bewertung, COUNT(*) FROM feedback
               GROUP BY bewertung ORDER BY count DESC"""
        )
        zeilen = cursor.fetchall()
        cursor.close()
        return {z[0]: z[1] for z in zeilen}

    # --- Statistiken ---

    def gesamtstatistik(self) -> dict:
        """Liefert eine Gesamtübersicht des Systems."""
        verbindung = self._verbinde()
        cursor = verbindung.cursor()

        cursor.execute("SELECT COUNT(*) FROM dokumente WHERE status = 'aktiv'")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM anfrage_protokoll")
        anfrage_count = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(konfidenz) FROM anfrage_protokoll")
        avg_conf = float(cursor.fetchone()[0] or 0)

        cursor.execute("SELECT COUNT(*) FROM feedback")
        fb_count = cursor.fetchone()[0]

        cursor.close()
        return {
            "dokumente": doc_count,
            "anfragen_gesamt": anfrage_count,
            "durchschnitt_konfidenz": round(avg_conf, 2),
            "feedback_gesamt": fb_count,
        }
