#!/bin/bash
# Skript zur vollständigen Neuindizierung aller Dokumente
# Nutzung: bash scripts/reindex.sh

set -euo pipefail

LOG_DATEI="reindex_$(date +%Y%m%d_%H%M%S).log"

echo "=== Neuindizierung gestartet: $(date) ===" | tee "$LOG_DATEI"
echo "==========================================" | tee -a "$LOG_DATEI"

# Umgebungsvariablen laden
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "[INFO] .env geladen" | tee -a "$LOG_DATEI"
else
    echo "[WARNUNG] .env nicht gefunden — Standardwerte verwendet" | tee -a "$LOG_DATEI"
fi

# 1. Python-Abhängigkeiten prüfen
echo "[1/4] Python-Abhängigkeiten prüfen..." | tee -a "$LOG_DATEI"
python3 -c "
import sys
fehler = []
try:
    import chromadb
except ImportError:
    fehler.append('chromadb')
try:
    from pypdf2 import PdfReader
except ImportError:
    fehler.append('pypdf2')
try:
    from docx import Document
except ImportError:
    fehler.append('python-docx')
if fehler:
    print(f'Fehlende Module: {fehler}')
    sys.exit(1)
print('Alle Module vorhanden.')
" 2>&1 | tee -a "$LOG_DATEI"

# 2. ChromaDB-Verzeichnis zurücksetzen
echo "[2/4] ChromaDB-Verzeichnis zurücksetzen..." | tee -a "$LOG_DATEI"
CHROMA_PFAD="${CHROMA_PATH:-.chroma}"
if [ -d "$CHROMA_PFAD" ]; then
    rm -rf "$CHROMA_PFAD"
    echo "  Altes Verzeichnis entfernt." | tee -a "$LOG_DATEI"
fi
mkdir -p "$CHROMA_PFAD"
echo "  Neues Verzeichnis erstellt." | tee -a "$LOG_DATEI"

# 3. Neuindizierung durchführen
echo "[3/4] Neuindizierung durchführen..." | tee -a "$LOG_DATEI"
python3 -c "
import os, sys
sys.path.insert(0, '.')
from rag.document_loader import DocumentLoader
from rag.chunker import TextChunker
from rag.vector_store import VectorStoreManager

data_pfad = os.environ.get('DATA_PATH', './data')
loader = DocumentLoader(data_pfad)
chunker = TextChunker()
store = VectorStoreManager(os.environ.get('CHROMA_PATH', '.chroma'))

store.erstelle_index()
alle_chunks = []
dokument_count = 0

for datei in os.listdir(data_pfad):
    if not any(datei.endswith(ext) for ext in ['.pdf', '.docx', '.txt', '.md']):
        continue
    pfad = os.path.join(data_pfad, datei)
    try:
        ergebnis = loader.lade_dokument(pfad)
        chunks = chunker.zerlege_text(ergebnis['text'], ergebnis['metadaten'])
        alle_chunks.extend(chunks)
        dokument_count += 1
        print(f'  Verarbeitet: {datei} ({len(chunks)} Abschnitte)')
    except Exception as e:
        print(f'  FEHLER bei {datei}: {e}')

eingefuegt = store.füge_dokumente_hinzu(alle_chunks)
print(f'\nErgebnis: {dokument_count} Dokumente, {eingefuegt} Abschnitte indiziert.')
" 2>&1 | tee -a "$LOG_DATEI"

# 4. Statistik anzeigen
echo "[4/4] Index-Statistik:" | tee -a "$LOG_DATEI"
python3 -c "
import os, sys
sys.path.insert(0, '.')
from rag.vector_store import VectorStoreManager
store = VectorStoreManager(os.environ.get('CHROMA_PATH', '.chroma'))
stat = store.index_statistik()
print(f'  Sammlung: {stat[\"sammlung\"]}')
print(f'  Abschnitte: {stat[\"anzahl_chunks\"]}')
print(f'  Verzeichnis: {stat[\"verzeichnis\"]}')
" 2>&1 | tee -a "$LOG_DATEI"

echo "=== Neuindizierung abgeschlossen: $(date) ===" | tee -a "$LOG_DATEI"
exit 0
