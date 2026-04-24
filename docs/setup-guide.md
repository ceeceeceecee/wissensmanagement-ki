# Setup-Guide — Schritt-für-Schritt Installation

## Voraussetzungen

- Linux-Server (Ubuntu 22.04+ empfohlen) oder macOS
- 4 CPU-Kerne (8+ empfohlen)
- 8 GB RAM (16+ empfohlen)
- 20 GB freier Festplattenspeicher
- Docker und Docker Compose (optional)

## Option A: Lokale Installation

### 1. Python installieren
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# macOS (mit Homebrew)
brew install python@3.11
```

### 2. Ollama installieren und Modell laden
```bash
# Ollama installieren
curl -fsSL https://ollama.ai/install.sh | sh

# Ollama starten
ollama serve &

# Modell herunterladen (ca. 4.7 GB)
ollama pull llama3

# Funktionstest
ollama run llama3 "Hallo, wer bist du?"
```

### 3. Projekt einrichten
```bash
# Repository klonen
git clone https://github.com/ceeceeceecee/wissensmanagement-ki.git
cd wissensmanagement-ki

# Virtuelle Umgebung erstellen
python3.11 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen einrichten
cp .env.example .env
# .env anpassen (nano .env)
```

### 4. PostgreSQL einrichten
```bash
# PostgreSQL installieren
sudo apt install postgresql postgresql-contrib -y

# Datenbank und Benutzer erstellen
sudo -u postgres psql
CREATE USER wissens WITH PASSWORD 'wissens';
CREATE DATABASE wissensmanagement OWNER wissens;
\q
```

### 5. Datenbank initialisieren
```bash
# Datenbankschema laden
PGPASSWORD=wissens psql -U wissens -d wissensmanagement -f database/schema.sql
```

### 6. Anwendung starten
```bash
streamlit run app.py
```
Die Anwendung ist unter `http://localhost:8501` erreichbar.

## Option B: Docker-Installation

### 1. Docker installieren
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Neue Anmeldung erforderlich
```

### 2. Ollama installieren (Host, für GPU-Zugriff)
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3
```

### 3. Projekt starten
```bash
git clone https://github.com/ceeceeceecee/wissensmanagement-ki.git
cd wissensmanagement-ki

# .env anpassen — OLLAMA_HOST auf http://host.docker.internal:11434
cp .env.example .env

docker compose up -d
```

### 4. Status prüfen
```bash
docker compose ps
docker compose logs app
```

## Erste Dokumente importieren

### 1. Dokumente vorbereiten
- Nur maschinenlesbare Dokumente (Text-PDFs, DOCX, TXT, MD)
- Keine eingescannten Bilder
- Aktuelle und gültige Dokumente

### 2. Dokumente hochladen
1. Öffnen Sie `http://localhost:8501` im Browser
2. Gehen Sie zum Tab "Dokumente verwalten"
3. Laden Sie die Dokumente hoch
4. Wählen Sie die passende Vertraulichkeitsstufe

### 3. Testanfragen durchführen
Beispielanfragen für den Test:
- "Wie beantrage ich einen Bauantrag?"
- "Welche Unterlagen werden für die Kindergeldzahlung benötigt?"
- "Was sind die Öffnungszeiten des Bürgeramts?"
- "Wie funktioniert der Widerspruchsverfahren?"

## Fehlerbehebung

### Ollama nicht erreichbar
```bash
# Status prüfen
curl http://localhost:11434/api/tags

# Neustart
systemctl restart ollama
```

### Datenbankverbindung fehlgeschlagen
```bash
# Verbindung testen
PGPASSWORD=wissens psql -U wissens -h localhost -d wissensmanagement -c "SELECT 1;"
```

### ChromaDB Fehler
```bash
# Verzeichnis zurücksetzen
rm -rf .chroma
# Neuindizierung durchführen
bash scripts/reindex.sh
```
