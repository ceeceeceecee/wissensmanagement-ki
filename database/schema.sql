-- Datenbankschema für kommunales Wissensmanagement
-- PostgreSQL-kompatibel

-- Tabelle für hochgeladene Dokumente
CREATE TABLE IF NOT EXISTS dokumente (
    id SERIAL PRIMARY KEY,
    titel VARCHAR(500) NOT NULL,
    dateiname VARCHAR(255) NOT NULL,
    abteilung VARCHAR(200) DEFAULT 'Unbekannt',
    version VARCHAR(50) DEFAULT '1.0',
    format VARCHAR(20) NOT NULL,
    zeichenanzahl INTEGER DEFAULT 0,
    hochladedatum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'aktiv',
    dateipfad VARCHAR(1000),
    UNIQUE(dateiname, version)
);

-- Tabelle für Textabschnitte (Chunks)
CREATE TABLE IF NOT EXISTS abschnitte (
    id SERIAL PRIMARY KEY,
    dokument_id INTEGER REFERENCES dokumente(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    ueberschrift VARCHAR(500),
    zeichenanzahl INTEGER DEFAULT 0,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Dokument-Tags (Vertraulichkeitsstufen, Kategorien)
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    dokument_id INTEGER REFERENCES dokumente(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dokument_id, tag)
);

-- Tabelle für Benutzer (Demo-Modell)
CREATE TABLE IF NOT EXISTS benutzer (
    id SERIAL PRIMARY KEY,
    benutzername VARCHAR(200) NOT NULL UNIQUE,
    rolle VARCHAR(50) DEFAULT 'sachbearbeitung',
    abteilung VARCHAR(200),
    aktiv BOOLEAN DEFAULT TRUE,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Rollendefinitionen
CREATE TABLE IF NOT EXISTS rollen (
    id SERIAL PRIMARY KEY,
    rolle VARCHAR(50) NOT NULL UNIQUE,
    beschreibung VARCHAR(500),
    berechtigungsstufen TEXT[] DEFAULT ARRAY['oeffentlich', 'intern']
);

-- Tabelle für Anfrage-Protokoll
CREATE TABLE IF NOT EXISTS anfrage_protokoll (
    id SERIAL PRIMARY KEY,
    frage TEXT NOT NULL,
    antwort TEXT,
    benutzer VARCHAR(200),
    rolle VARCHAR(50),
    quellenanzahl INTEGER DEFAULT 0,
    konfidenz NUMERIC(5,4) DEFAULT 0,
    verarbeitungszeit_ms INTEGER DEFAULT 0,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    anfrage_id INTEGER REFERENCES anfrage_protokoll(id),
    bewertung VARCHAR(20) NOT NULL,
    kommentar TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_dokumente_abteilung ON dokumente(abteilung);
CREATE INDEX IF NOT EXISTS idx_dokumente_status ON dokumente(status);
CREATE INDEX IF NOT EXISTS idx_abschnitte_dokument ON abschnitte(dokument_id);
CREATE INDEX IF NOT EXISTS idx_tags_dokument ON tags(dokument_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_anfrage_protokoll_datum ON anfrage_protokoll(erstellt_am);
CREATE INDEX IF NOT EXISTS idx_anfrage_protokoll_rolle ON anfrage_protokoll(rolle);

-- Standard-Rollen einfügen
INSERT INTO rollen (rolle, beschreibung, berechtigungsstufen) VALUES
    ('sachbearbeitung', 'Standard-Rolle für Sachbearbeitung', ARRAY['oeffentlich', 'intern']),
    ('teamleitung', 'Erweiterte Rolle für Teamleitungen', ARRAY['oeffentlich', 'intern', 'fachbereich']),
    ('admin', 'Vollzugriff für Verwaltung', ARRAY['oeffentlich', 'intern', 'fachbereich', 'vertraulich'])
ON CONFLICT (rolle) DO NOTHING;
