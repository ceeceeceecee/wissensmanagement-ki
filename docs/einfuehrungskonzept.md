# Einführungskonzept — Pilotbetrieb

## Zielsetzung

Das System soll schrittweise in einer Kommune eingeführt werden. Der Pilotbetrieb
in einem Fachbereich ermöglicht das Sammeln von Erfahrungen und die Optimierung
vor einer flächendeckenden Bereitstellung.

## Phase 1: Vorbereitung (Woche 1-2)

### Fachbereich auswählen
Empfohlene Fachbereiche für den Pilotbetrieb:
- Jugendamt (viele wiederkehrende Fragen, klare Regeldokumente)
- Bauamt (viele Vorschriften, Formulare, Gebührenordnungen)
- Ordnungsamt (Dienstvorschriften, Satzungen)

### Dokumentenauswahl
- 20-50 repräsentative Dokumente aus dem gewählten Fachbereich
- Dienstvorschriften, Verwaltungsvorschriften, Satzungen
- Formulare und Merkblätter
- FAQ-Sammlungen und Prozessbeschreibungen

### Qualität der Dokumente
- Dokumente müssen maschinenlesbar sein (keine eingescannten Bilder)
- PDFs sollten Text enthalten (keine reinen Scans)
- Dokumente sollten aktuell und gültig sein
- Veraltete Dokumente vorher aussortieren

## Phase 2: Technik-Setup (Woche 2-3)

### Installation
1. Server bereitstellen (siehe Setup-Guide)
2. Docker und Ollama installieren
3. KI-Modell herunterladen: `ollama pull llama3`
4. Anwendung starten und erreichbar machen
5. Erste Testanfragen durchführen

### Rollen zuweisen
| Rolle | Anzahl | Beschreibung |
|---|---|---|
| admin | 1-2 | IT-Verwaltung, Systembetreuung |
| teamleitung | 2-3 | Fachbereichsleitung |
| sachbearbeitung | 5-10 | Pilot-Teilnehmende |

## Phase 3: Pilotbetrieb (Woche 3-8)

### Testphase (Woche 3-4)
- Kleine Gruppe (3-5 Personen) testet das System
- Tägliche Nutzung mit realen Fragen
- Dokumentation von Problemen und Verbesserungsvorschlägen

### Erweiterte Nutzung (Woche 5-6)
- Gruppe auf 5-10 Personen erweitern
- Weitere Dokumente hinzufügen
- Nutzungsauswertung durchführen

### Evaluierung (Woche 7-8)
- Auswertung der Nutzungsauswertung
- Analyse unbeantworteter Anfragen
- Qualitative Befragung der Teilnehmenden
- Entscheidung über Fortführung oder Anpassung

## Phase 4: Feedback-Schleife

### Wöchentliche Rücksprache
- Kurzes Meeting (30 Min) mit den Pilot-Teilnehmenden
- Besprechung offener Fragen und Probleme
- Priorisierung von Verbesserungen

### Dokument-Qualität prüfen
- Welche Dokumente werden häufig als Quelle zitiert?
- Welche Fragen können nicht beantwortet werden?
- Fehlen wichtige Dokumente im System?

### KI-Antwort-Qualität
- Sind die Antworten hilfreich und korrekt?
- Wird die Konfidenz angemessen bewertet?
- Werden Quellen korrekt angegeben?

## Erfolgsindikatoren

| Indikator | Ziel |
|---|---|
| Antworten mit hoher Konfidenz (>60%) | >70% |
| Durchschnittliche Nutzerzufriedenheit | >3,5/5 |
| Anfragen pro Woche | >20 |
| Unbeantwortete Anfragen | <15% |
| Zeitersparnis (geschätzt) | >30% |

## Nächste Schritte nach dem Pilot

1. Auswertung und Bericht an die Leitung
2. Entscheidung über Ausweitung auf weitere Fachbereiche
3. Integration in bestehende IT-Infrastruktur
4. Schulung weiterer Mitarbeitender
5. Dauerverwaltung und Wartung etablieren
