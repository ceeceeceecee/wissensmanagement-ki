# Datenschutz und Datensicherheit

## Übersicht

Das System "Kommunales Wissensmanagement mit RAG" wurde von Grund auf DSGVO-konform
entwickelt. Alle Daten werden ausschließlich lokal verarbeitet — es findet keine
Datenübertragung an externe Cloud-Dienste statt.

## Datenspeicherung

### Dokumente
- Hochgeladene Dokumente werden im lokalen Dateisystem gespeichert (Pfad: `data/`).
- Nach der Textextraktion werden die Dokumente in Textabschnitte (Chunks) zerlegt.
- Die Chunks werden in einer lokalen ChromaDB-Instanz als Vektoren gespeichert.
- Metadaten (Titel, Abteilung, Tags) werden in PostgreSQL gespeichert.

### Vektordatenbank (ChromaDB)
- ChromaDB läuft lokal im Docker-Container oder auf dem Host.
- Vektoren werden im Persistenzverzeichnis (`.chroma/`) gespeichert.
- Es erfolgt keine Datenübertragung an externe Dienste.

### Anfrageprotokoll
- Alle Anfragen werden mit Zeitstempel protokolliert.
- Keine personenbezogenen Daten werden gespeichert (nur Anfragetext und Rolle).
- Siehe Löschkonzept unten.

### KI-Verarbeitung (Ollama)
- Ollama läuft ausschließlich lokal auf dem Server der Kommune.
- Keine Anfrage wird an externe KI-Dienste gesendet.
- Das Sprachmodell wird einmalig heruntergeladen und lokal ausgeführt.

## Umgang mit vertraulichen Dokumenten

### Vertraulichkeitsstufen
1. **Öffentlich** — Für alle Rollen zugänglich
2. **Intern** — Für alle internen Mitarbeitenden
3. **Fachbereich** — Nur für Teamleitungen und Verwaltung
4. **Vertraulich** — Nur für Verwaltungsrolle (Admin)

### Empfehlungen
- Vertrauliche Dokumente sollten nur nach Prüfung hochgeladen werden.
- Personenbezogene Daten sollten aus Dokumenten entfernt werden, bevor sie
  hochgeladen werden.
- Das System sollte im internen Netzwerk betrieben werden (kein direkter
  Internetzugriff).

## Löschkonzept

### Automatische Löschung
- Anfrageprotokolle werden nach 12 Monaten automatisch gelöscht.
- Feedback-Daten werden nach 6 Monaten anonymisiert.

### Manuelle Löschung
- Dokumente können jederzeit über die Oberfläche gelöscht werden.
- Bei Löschung werden auch alle zugehörigen Chunks aus ChromaDB entfernt.
- Die Vektordatenbank kann komplett zurückgesetzt werden (Neuindizierung).

### Datenlöschung bei Beendigung
Bei Beendigung der Nutzung des Systems:
1. Alle Dokumente aus `data/` löschen
2. ChromaDB-Verzeichnis (`.chroma/`) löschen
3. PostgreSQL-Datenbank leeren
4. Docker-Volumes entfernen: `docker compose down -v`

## Netzwerk und Zugriff

### Empfohlene Netzwerkkonfiguration
- Betrieb ausschließlich im internen Netzwerk (LAN/Intranet)
- Keine Öffnung nach außen (kein Port-Forwarding)
- HTTPS mit internem Zertifikat empfohlen
- Zugriff nur über VPN bei Fernzugriff

### Zugriffsprotokollierung
- Alle Anfragen werden in der Datenbank protokolliert
- Zeitstempel und Rolle werden erfasst
- Keine Speicherung von IP-Adressen oder Benutzernamen (im Demo-Modus)

## Technische Maßnahmen

- Rollenbasiertes Zugriffskontrollsystem (RBAC)
- Vertrauliche Dokumente werden vor der Suche gefiltert
- Guardrail-System blockiert sensible Anfragen (Rechtsberatung, etc.)
- Konfidenzbewertung warnt bei unsicheren Antworten
