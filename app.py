"""
Kommunales Wissensmanagement mit RAG — Streamlit Weboberfläche
"""

import os
import sys
import time
import tempfile
from datetime import datetime

import streamlit as st

# RAG-Module laden
from rag.document_loader import DocumentLoader
from rag.chunker import TextChunker
from rag.vector_store import VectorStoreManager
from rag.answer_engine import AnswerEngine
from rag.permissions import PermissionManager

# Umgebungsvariabten
DATA_PATH = os.getenv("DATA_PATH", "./data")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./.chroma")
UPLOAD_PATH = os.getenv("UPLOAD_PATH", "./uploads")
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(UPLOAD_PATH, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

# Seitenkonfiguration
st.set_page_config(
    page_title="Kommunales Wissensmanagement",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session State initialisieren
if "chat_verlauf" not in st.session_state:
    st.session_state.chat_verlauf = []
if "aktuelle_rolle" not in st.session_state:
    st.session_state.aktuelle_rolle = "sachbearbeitung"


def initialisiere_komponenten():
    """Initialisiert alle RAG-Komponenten (Lazy)."""
    if "loader" not in st.session_state:
        st.session_state.loader = DocumentLoader(UPLOAD_PATH)
    if "chunker" not in st.session_state:
        st.session_state.chunker = TextChunker()
    if "store" not in st.session_state:
        st.session_state.store = VectorStoreManager(CHROMA_PATH)
        st.session_state.store.erstelle_index()
    if "engine" not in st.session_state:
        st.session_state.engine = AnswerEngine()
    if "perms" not in st.session_state:
        st.session_state.perms = PermissionManager()
    st.session_state.perms.setze_rolle(st.session_state.aktuelle_rolle)


def zeige_sidebar():
    """Zeigt die Seitenleiste mit Rolle und Systeminfo."""
    with st.sidebar:
        st.image("🏛️", width=80)
        st.title("Wissensmanagement")
        st.caption("Kommunale Verwaltung")

        st.divider()

        # Rollenauswahl
        st.subheader("👤 Aktive Rolle")
        rollen = st.session_state.perms.gib_alle_rollen()
        aktuelle = st.session_state.aktuelle_rolle
        for rolle in rollen:
            if st.button(rolle.replace("_", " ").title(), use_container_width=True,
                         type="primary" if rolle == aktuelle else "secondary"):
                st.session_state.aktuelle_rolle = rolle
                st.session_state.perms.setze_rolle(rolle)
                st.rerun()

        erlaubt = st.session_state.perms.gib_erlaubte_stufen()
        st.caption(f"Erlaubt: {', '.join(erlaubt)}")

        st.divider()

        # Systemstatus
        st.subheader("📊 Systemstatus")
        try:
            stat = st.session_state.store.index_statistik()
            st.metric("Indizierte Abschnitte", stat["anzahl_chunks"])
        except Exception:
            st.warning("Index nicht verfügbar")

        try:
            import requests
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            antwort = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if antwort.status_code == 200:
                modelle = [m["name"] for m in antwort.json().get("models", [])]
                st.metric("Verfügbare Modelle", len(modelle))
                for modell in modelle[:3]:
                    st.caption(f"• {modell}")
            else:
                st.error("Ollama nicht erreichbar")
        except Exception:
            st.error("Ollama nicht erreichbar")


def seite_chat():
    """Chat-Seite: Fragen an den Wissensbestand stellen."""
    st.header("🔎 Frag die Verwaltung")
    st.caption("Stellen Sie eine Frage an den internen Wissensbestand.")

    # Chat-Verlauf anzeigen
    for nachricht in st.session_state.chat_verlauf:
        with st.chat_message(nachricht["rolle"]):
            st.markdown(nachricht["inhalt"])
            if "quellen" in nachricht and nachricht["quellen"]:
                with st.expander("📚 Quellen"):
                    for quelle in nachricht["quellen"]:
                        st.markdown(f"- **{quelle['titel']}** — {quelle['dateiname']} (Relevanz: {quelle['relevanz']:.0%})")
            if "warnung" in nachricht and nachricht["warnung"]:
                st.warning(nachricht["warnung"])
            if "konfidenz" in nachricht:
                st.caption(f"Konfidenz: {nachricht['konfidenz']:.0%}")

    # Eingabefeld
    if frage := st.chat_input("Ihre Frage..."):
        # Nutzernachricht anzeigen
        st.session_state.chat_verlauf.append({"rolle": "user", "inhalt": frage})
        with st.chat_message("user"):
            st.markdown(frage)

        # Antwort generieren
        with st.chat_message("assistant"):
            with st.spinner("Suche nach relevanten Dokumenten..."):
                start = time.time()

                # Berechtigungsgerechte Suche
                treffer = st.session_state.store.suche(frage, n_ergebnisse=5)
                gefiltert = st.session_state.perms.filtere_treffer(treffer)

                # Antwort generieren
                ergebnis = st.session_state.engine.generiere_antwort(
                    frage=frage,
                    treffer=gefiltert,
                    rolle=st.session_state.aktuelle_rolle,
                )

                dauer = int((time.time() - start) * 1000)

            st.markdown(ergebnis["antwort"])

            if ergebnis["quellen"]:
                with st.expander("📚 Quellen"):
                    for quelle in ergebnis["quellen"]:
                        st.markdown(
                            f"- **{quelle['titel']}** — {quelle['dateiname']} "
                            f"(Relevanz: {quelle['relevanz']:.0%})"
                        )

            if ergebnis["warnung"]:
                st.warning(ergebnis["warnung"])

            st.caption(f"Konfidenz: {ergebnis['konfidenz']:.0%} | Dauer: {dauer}ms")

            # Zum Verlauf hinzufügen
            st.session_state.chat_verlauf.append({
                "rolle": "assistant",
                "inhalt": ergebnis["antwort"],
                "quellen": ergebnis["quellen"],
                "konfidenz": ergebnis["konfidenz"],
                "warnung": ergebnis["warnung"],
            })

    # Verlauf löschen
    if st.session_state.chat_verlauf and st.button("💬 Chat-Verlauf löschen"):
        st.session_state.chat_verlauf = []
        st.rerun()


def seite_dokumente():
    """Dokumentverwaltung: Hochladen, Taggen, Status anzeigen."""
    st.header("📚 Dokumente verwalten")
    st.caption("Laden Sie Verwaltungsdokumente hoch und verwalten Sie diese.")

    tab_upload, tab_liste = st.tabs(["📤 Hochladen", "📋 Dokumentliste"])

    with tab_upload:
        hochgeladene = st.file_uploader(
            "Dokument auswählen",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
        )

        if hochgeladene:
            st.subheader("Dokument-Details")
            abteilung = st.text_input("Abteilung", placeholder="z.B. Jugendamt, Bauamt")
            tag = st.selectbox(
                "Vertraulichkeitsstufe",
                ["oeffentlich", "intern", "fachbereich", "vertraulich"],
                format_func=lambda x: {
                    "oeffentlich": "Öffentlich",
                    "intern": "Intern",
                    "fachbereich": "Fachbereich",
                    "vertraulich": "Vertraulich",
                }[x],
            )

            if st.button("📤 Dokumente hochladen und indizieren", type="primary"):
                for datei in hochgeladene:
                    try:
                        # Datei speichern
                        speicher_pfad = os.path.join(UPLOAD_PATH, datei.name)
                        with open(speicher_pfad, "wb") as f:
                            f.write(datei.getbuffer())

                        # Dokument laden
                        ergebnis = st.session_state.loader.lade_dokument(
                            speicher_pfad,
                            abteilung=abteilung,
                        )

                        # Tag zum Metadaten hinzufügen
                        ergebnis["metadaten"]["tags"] = [tag]

                        # Chunking
                        chunks = st.session_state.chunker.zerlege_text(
                            ergebnis["text"], ergebnis["metadaten"]
                        )

                        # Zum Vektorindex hinzufügen
                        st.session_state.store.füge_dokumente_hinzu(chunks)

                        st.success(f"✅ {datei.name} — {len(chunks)} Abschnitte indiziert")

                    except Exception as e:
                        st.error(f"❌ Fehler bei {datei.name}: {e}")

    with tab_liste:
        try:
            stat = st.session_state.store.index_statistik()
            st.metric("Indizierte Abschnitte", stat["anzahl_chunks"])
        except Exception:
            st.warning("Index nicht verfügbar")

        # Hochgeladene Dateien anzeigen
        if os.path.exists(UPLOAD_PATH):
            dateien = [
                f for f in os.listdir(UPLOAD_PATH)
                if any(f.endswith(ext) for ext in [".pdf", ".docx", ".txt", ".md"])
            ]
            if dateien:
                for datei in dateien:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 {datei}")
                    with col2:
                        if st.button("🗑️", key=f"del_{datei}"):
                            try:
                                st.session_state.store.lösche_dokument(datei)
                                st.success(f"{datei} gelöscht")
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                            st.rerun()
            else:
                st.info("Keine Dokumente hochgeladen.")


def seite_index():
    """Index-Verwaltung: Neuindizierung und Fehleranalyse."""
    st.header("🧠 Index-Verwaltung")
    st.caption("Verwalten Sie den Vektordatenbank-Index.")

    try:
        stat = st.session_state.store.index_statistik()
        st.metric("Aktuelle Abschnitte im Index", stat["anzahl_chunks"])
    except Exception:
        st.error("Index nicht verfügbar")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔄 Neuindizierung")
        st.warning("⚠️ Dies löscht den aktuellen Index und erstellt ihn neu.")
        if st.button("Komplett neu indizieren", type="primary"):
            with st.spinner("Indiziere alle Dokumente neu..."):
                try:
                    alle_chunks = []
                    if os.path.exists(UPLOAD_PATH):
                        for datei in os.listdir(UPLOAD_PATH):
                            if not any(datei.endswith(ext) for ext in [".pdf", ".docx", ".txt", ".md"]):
                                continue
                            pfad = os.path.join(UPLOAD_PATH, datei)
                            try:
                                ergebnis = st.session_state.loader.lade_dokument(pfad)
                                chunks = st.session_state.chunker.zerlege_text(
                                    ergebnis["text"], ergebnis["metadaten"]
                                )
                                alle_chunks.extend(chunks)
                            except Exception as e:
                                st.error(f"Fehler bei {datei}: {e}")

                    if alle_chunks:
                        st.session_state.store.reindiziere(alle_chunks)
                        st.success(f"✅ {len(alle_chunks)} Abschnitte neu indiziert.")
                    else:
                        st.info("Keine Dokumente zum Indizieren gefunden.")

                except Exception as e:
                    st.error(f"Neuindizierung fehlgeschlagen: {e}")

    with col2:
        st.subheader("📈 Index-Details")
        st.write(f"**Sammlung:** {stat.get('sammlung', 'N/A')}")
        st.write(f"**Verzeichnis:** {stat.get('verzeichnis', 'N/A')}")
        st.write(f"**Abschnitte:** {stat.get('anzahl_chunks', 0)}")


def seite_rollen():
    """Rollen und Berechtigungsmodell anzeigen."""
    st.header("👥 Rollen & Zugriff")
    st.caption("Übersicht über das Berechtigungsmodell.")

    st.subheader("Berechtigungsmatrix")
    matrix = st.session_state.perms.gib_berechtigungsmatrix()

    # Matrix als Tabelle anzeigen
    stufen = ["oeffentlich", "intern", "fachbereich", "vertraulich"]
    stufen_labels = {
        "oeffentlich": "Öffentlich",
        "intern": "Intern",
        "fachbereich": "Fachbereich",
        "vertraulich": "Vertraulich",
    }

    tabelle_daten = []
    for rolle, erlaubt in matrix.items():
        zeile = {"Rolle": rolle.replace("_", " ").title()}
        for stufe in stufen:
            zeile[stufen_labels[stufe]] = "✅" if stufe in erlaubt else "❌"
        tabelle_daten.append(zeile)

    st.dataframe(tabelle_daten, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Aktuelle Rolle")
    st.info(f"Angemeldet als: **{st.session_state.aktuelle_rolle.replace('_', ' ').title()}**")
    erlaubt = st.session_state.perms.gib_erlaubte_stufen()
    st.write(f"Erlaubte Stufen: {', '.join(erlaubt)}")


def seite_auswertung():
    """Nutzungsauswertung: Häufige Anfragen, unbeantwortete Fragen."""
    st.header("📊 Nutzungsauswertung")
    st.caption("Analysieren Sie die Nutzung des Wissensmanagements.")

    tab_häufig, tab_unbeantwortet, tab_feedback = st.tabs(
        [" häufige Anfragen", "❓ Unbeantwortet", "💬 Feedback"]
    )

    with tab_häufig:
        st.subheader("Meistgestellte Fragen")
        st.info("Basierend auf dem Chat-Verlauf der aktuellen Sitzung.")

        if st.session_state.chat_verlauf:
            fragen = {}
            for nachricht in st.session_state.chat_verlauf:
                if nachricht["rolle"] == "user":
                    frage = nachricht["inhalt"]
                    fragen[frage] = fragen.get(frage, 0) + 1

            sortiert = sorted(fragen.items(), key=lambda x: x[1], reverse=True)
            for frage, anzahl in sortiert[:10]:
                st.write(f"**{anzahl}x** — {frage}")
        else:
            st.info("Noch keine Anfragen in dieser Sitzung.")

    with tab_unbeantwortet:
        st.subheader("Möglicherweise unbeantwortete Anfragen")
        st.caption("Antworten mit niedriger Konfidenz.")

        unbeantwortet = [
            n for n in st.session_state.chat_verlauf
            if n["rolle"] == "assistant" and n.get("konfidenz", 1) < 0.4
        ]

        if unbeantwortet:
            for nachricht in unbeantwortet:
                st.warning(f"Konfidenz: {nachricht['konfidenz']:.0%} — {nachricht['inhalt'][:100]}...")
        else:
            st.success("Keine Anfragen mit niedriger Konfidenz.")

    with tab_feedback:
        st.subheader("Feedback")
        st.caption("Bewertungen zu den Antworten.")

        if st.session_state.chat_verlauf:
            for i, nachricht in enumerate(st.session_state.chat_verlauf):
                if nachricht["rolle"] == "assistant":
                    col1, col2, col3 = st.columns([5, 1, 1])
                    with col1:
                        st.text(nachricht["inhalt"][:80] + "...")
                    with col2:
                        if st.button("👍", key=f"up_{i}"):
                            st.success("Danke für das Feedback!")
                    with col3:
                        if st.button("👎", key=f"down_{i}"):
                            st.info("Danke — wir werden das verbessern.")
        else:
            st.info("Noch keine Antworten zum Bewerten.")


# --- Hauptprogramm ---
def main():
    initialisiere_komponenten()
    zeige_sidebar()

    # Tabs
    tab_chat, tab_docs, tab_index, tab_rollen, tab_stats = st.tabs([
        "🔎 Frag die Verwaltung",
        "📚 Dokumente verwalten",
        "🧠 Index-Verwaltung",
        "👥 Rollen & Zugriff",
        "📊 Nutzungsauswertung",
    ])

    with tab_chat:
        seite_chat()

    with tab_docs:
        seite_dokumente()

    with tab_index:
        seite_index()

    with tab_rollen:
        seite_rollen()

    with tab_stats:
        seite_auswertung()


if __name__ == "__main__":
    main()
