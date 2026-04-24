"""
Vektordatenbank-Verwaltung mit ChromaDB
Lokale Speicherung — keine Cloud-Dienste.
"""

import os
from typing import List, Optional


class VectorStoreManager:
    """Verwaltung der Vektordatenbank mit ChromaDB (lokal)."""

    def __init__(self, persistenz_verzeichnis: str = ".chroma"):
        self.persistenz_verzeichnis = persistenz_verzeichnis
        os.makedirs(persistenz_verzeichnis, exist_ok=True)
        self._client = None
        self._sammlung = None

    def _initialisiere(self):
        """Initialisiert ChromaDB bei Bedarf (Lazy Loading)."""
        if self._client is not None:
            return

        import chromadb

        self._client = chromadb.PersistentClient(path=self.persistenz_verzeichnis)

    def erstelle_index(self, sammlungs_name: str = "verwaltungsdokumente"):
        """Erstellt einen neuen Vektorindex."""
        self._initialisiere()
        self._sammlung = self._client.get_or_create_collection(
            name=sammlungs_name,
            metadata={"beschreibung": "Kommunaler Wissensbestand"},
        )
        return self._sammlung

    def füge_dokumente_hinzu(
        self,
        chunks: List[dict],
        sammlungs_name: str = "verwaltungsdokumente",
    ) -> int:
        """Fügt Textabschnitte zum Index hinzu."""
        if not chunks:
            return 0

        self._initialisiere()
        self._sammlung = self._client.get_or_create_collection(name=sammlungs_name)

        ids = []
        dokumente = []
        metadaten = []

        for chunk in chunks:
            chunk_id = f"{chunk['metadaten'].get('dateiname', 'unbekannt')}_{chunk['metadaten'].get('chunk_index', 0)}"
            ids.append(chunk_id)
            dokumente.append(chunk["text"])
            metadaten.append(chunk["metadaten"])

        # In Batches einfügen (ChromaDB empfiehlt max. ~500 pro Batch)
        batch_größe = 100
        eingefügt = 0

        for i in range(0, len(ids), batch_größe):
            batch_ids = ids[i : i + batch_größe]
            batch_docs = dokumente[i : i + batch_größe]
            batch_meta = metadaten[i : i + batch_größe]

            self._sammlung.add(
                ids=batch_ids,
                documents=batch_docs,
                metadaten=batch_meta,
            )
            eingefügt += len(batch_ids)

        return eingefügt

    def suche(
        self,
        anfrage: str,
        n_ergebnisse: int = 5,
        sammlungs_name: str = "verwaltungsdokumente",
        filter_tags: Optional[List[str]] = None,
    ) -> List[dict]:
        """Sucht nach relevanten Textabschnitten."""
        self._initialisiere()

        try:
            self._sammlung = self._client.get_collection(name=sammlungs_name)
        except Exception:
            return []

        where_filter = None
        if filter_tags:
            where_filter = {"$or": [{"tags": tag} for tag in filter_tags]}

        ergebnisse = self._sammlung.query(
            query_texts=[anfrage],
            n_results=n_ergebnisse,
            where=where_filter,
        )

        treffer = []
        if ergebnisse and ergebnisse["documents"]:
            for i, doc in enumerate(ergebnisse["documents"][0]):
                metadaten = ergebnisse["metadaten"][0][i] if ergebnisse["metadaten"] else {}
                distanz = ergebnisse["distances"][0][i] if ergebnisse["distances"] else 0
                treffer.append({
                    "text": doc,
                    "metadaten": metadaten,
                    "relevanz": round(1 - distanz, 3) if distanz <= 1 else 0,
                    "distanz": round(distanz, 4),
                })

        return treffer

    def lösche_dokument(
        self,
        dateiname: str,
        sammlungs_name: str = "verwaltungsdokumente",
    ) -> int:
        """Löscht alle Abschnitte eines Dokuments."""
        self._initialisiere()

        try:
            self._sammlung = self._client.get_collection(name=sammlungs_name)
        except Exception:
            return 0

        # Alle IDs finden, die mit dem Dateinamen beginnen
        bestand = self._sammlung.get()
        zu_löschen = [
            doc_id
            for doc_id in bestand["ids"]
            if doc_id.startswith(dateiname)
        ]

        if zu_löschen:
            self._sammlung.delete(ids=zu_löschen)

        return len(zu_löschen)

    def reindiziere(
        self,
        chunks: List[dict],
        sammlungs_name: str = "verwaltungsdokumente",
    ) -> int:
        """Löscht bestehenden Index und erstellt neu."""
        self._initialisiere()

        try:
            self._client.delete_collection(name=sammlungs_name)
        except Exception:
            pass

        self._sammlung = None
        return self.füge_dokumente_hinzu(chunks, sammlungs_name)

    def index_statistik(self, sammlungs_name: str = "verwaltungsdokumente") -> dict:
        """Liefert Statistiken zum aktuellen Index."""
        self._initialisiere()

        try:
            self._sammlung = self._client.get_collection(name=sammlungs_name)
            bestand = self._sammlung.get()
            return {
                "anzahl_chunks": len(bestand["ids"]),
                "sammlung": sammlungs_name,
                "verzeichnis": self.persistenz_verzeichnis,
            }
        except Exception:
            return {
                "anzahl_chunks": 0,
                "sammlung": sammlungs_name,
                "verzeichnis": self.persistenz_verzeichnis,
            }
