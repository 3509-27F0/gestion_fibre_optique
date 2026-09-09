
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import base64
import hashlib
from pdf_utils import generate_pdf, pdf_preview

BASE = Path(__file__).parent
DB = BASE / "data" / "fibre.db"
UPLOADS = BASE / "uploads"
DB.parent.mkdir(exist_ok=True)
UPLOADS.mkdir(exist_ok=True)

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    with conn() as c:
        user = c.execute(
            "SELECT * FROM users WHERE username = ? AND actif = 1",
            (username,)
        ).fetchone()

    if user and user["password_hash"] == hash_password(password):
        return user

    return None

def init_db():
    with conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS interventions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE,
            date_intervention TEXT NOT NULL,
            techniciens TEXT,
            client TEXT,
            site TEXT,
            localisation TEXT,
            type_intervention TEXT,
            heure_debut TEXT,
            heure_fin TEXT,
            equipement TEXT,
            fibre_type TEXT,
            probleme TEXT,
            diagnostic TEXT,
            distance_defaut TEXT,
            puissance_avant TEXT,
            puissance_apres TEXT,
            travaux TEXT,
            materiel TEXT,
            resultat TEXT,
            recommandations TEXT,
            observations TEXT,
            cree_le TEXT NOT NULL
        )
        """)

def next_number():
    with conn() as c:
        row = c.execute("SELECT id FROM interventions ORDER BY id DESC LIMIT 1").fetchone()
    n = (row["id"] + 1) if row else 1
    return f"INT-{datetime.now():%Y}-{n:04d}"

def save_intervention(data):
    with conn() as c:
        c.execute("""
        INSERT INTO interventions (
            numero,date_intervention,techniciens,client,site,localisation,
            type_intervention,heure_debut,heure_fin,equipement,fibre_type,
            probleme,diagnostic,distance_defaut,puissance_avant,puissance_apres,
            travaux,materiel,resultat,recommandations,observations,cree_le,
            statut,created_by
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            *data,
            datetime.now().isoformat(timespec="seconds"),
            "Brouillon",
            st.session_state.user_id
        ))


init_db()
st.set_page_config(page_title="Gestion Fibre Optique | VIPNET", page_icon="🧵", layout="wide")
# -----------------------------------------------------------------------------
# AUTHENTIFICATION
# -----------------------------------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Connexion")
    st.write("Veuillez vous connecter pour accéder à Gestion Fibre Optique.")

    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            user = authenticate(username, password)

            if user:
                st.session_state.authenticated = True
                st.session_state.user_id = user["id"]
                st.session_state.username = user["username"]
                st.session_state.nom = user["nom"]
                st.session_state.role = user["role"]
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")

    st.stop()

# -----------------------------------------------------------------------------
# GESTION DES RÔLES ET PERMISSIONS
# -----------------------------------------------------------------------------

ROLE_PERMISSIONS = {
    "administrateur": {
        "nouvelle_intervention": True,
        "historique": True,
        "tableau_de_bord": True,
        "gestion_utilisateurs": True,
    },
    "chef": {
        "nouvelle_intervention": True,
        "historique": True,
        "tableau_de_bord": True,
        "gestion_utilisateurs": False,
    },
    "superviseur": {
        "nouvelle_intervention": True,
        "historique": True,
        "tableau_de_bord": True,
        "gestion_utilisateurs": False,
    },
    "technicien": {
        "nouvelle_intervention": True,
        "historique": True,
        "tableau_de_bord": True,
        "gestion_utilisateurs": False,
    },
    "sous-traitant": {
        "nouvelle_intervention": True,
        "historique": True,
        "tableau_de_bord": True,
        "gestion_utilisateurs": False,
    },
    "ingenieur": {
        "nouvelle_intervention": True,
        "historique": True,
        "tableau_de_bord": True,
        "gestion_utilisateurs": False,
    },
}

role = st.session_state.get("role", "technicien")
permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["technicien"])
# -----------------------------------------------------------------------------
# PERSONNALISATION VISUELLE
# Les fichiers sont stockés dans assets/ afin de fonctionner localement sur Kali.
# Aucun changement n'est apporté à la logique métier ou à la base SQLite.
# -----------------------------------------------------------------------------
LOGO = BASE / "assets" / "logo_vipnet.png"
BACKGROUND = BASE / "assets" / "arriere_plan_fibre.jpeg"

def image_data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"

if BACKGROUND.exists():
    background_uri = image_data_uri(BACKGROUND)
    st.markdown(
        f"""
        <style>
        /* Arrière-plan VIPNET fibre optique */
        .stApp {{
            background-image: linear-gradient(rgba(3, 20, 70, 0.62), rgba(3, 20, 70, 0.62)),
                              url(\"{background_uri}\");
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
        }}

        /* Zone principale légèrement translucide pour garder une excellente lisibilité */
        .main .block-container {{
            background: rgba(255, 255, 255, 0.94);
            border-radius: 18px;
            padding: 1.8rem 2rem 2.5rem 2rem;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.20);
        }}

        /* Sidebar */
        [data-testid=\"stSidebar\"] {{
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(239,245,255,0.97));
            border-right: 1px solid rgba(20, 61, 160, 0.15);
        }}

        /* Titres */
        h1, h2, h3 {{
            color: #0b3fa5 !important;
        }}

        /* Boutons principaux */
        div.stButton > button[kind=\"primary\"],
        div[data-testid=\"stFormSubmitButton\"] button[kind=\"primary\"] {{
            border-radius: 10px;
            font-weight: 700;
        }}

        /* En-tête logo */
        .vipnet-header {{
            display: flex;
            align-items: center;
            gap: 18px;
            margin-bottom: 0.4rem;
        }}
        .vipnet-header img {{
            width: 185px;
            max-width: 35vw;
            height: auto;
            border-radius: 8px;
            background: white;
        }}
        .vipnet-title {{
            font-size: clamp(1.5rem, 3vw, 2.35rem);
            font-weight: 800;
            color: #0b3fa5;
            line-height: 1.1;
        }}
        .vipnet-subtitle {{
            color: #52627a;
            margin-top: 5px;
            font-size: 0.95rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

if LOGO.exists():
    st.sidebar.image(str(LOGO), use_container_width=True)
    st.sidebar.markdown("### Gestion Fibre Optique")
    st.sidebar.caption("VIPNET • Solutions & Service Provider")
    st.sidebar.divider()

if LOGO.exists():
    logo_uri = image_data_uri(LOGO)
    st.markdown(
        f"""
        <div class=\"vipnet-header\">
            <img src=\"{logo_uri}\" alt=\"Logo VIPNET\">
            <div>
                <div class=\"vipnet-title\">GESTION DES INTERVENTIONS<br>FIBRE OPTIQUE</div>
                <div class=\"vipnet-subtitle\">Journal de traçabilité • fonctionnement local • SQLite • version 1</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.title("🧵 GESTION DES INTERVENTIONS — FIBRE OPTIQUE")
    st.caption("Journal de traçabilité • fonctionnement local • SQLite • version 1")

menu_options = ["Tableau de bord", "Nouvelle intervention", "Historique"]

if permissions["gestion_utilisateurs"]:
    menu_options.append("Gestion des utilisateurs")

menu = st.sidebar.radio("MENU", menu_options)
if menu == "Nouvelle intervention":
    st.header("➕ Nouvelle intervention")
    st.info("Chaque intervention est ajoutée à l'historique. Les anciennes fiches ne sont pas écrasées.")
    numero = next_number()
    st.write(f"**Numéro automatique : {numero}**")

    with st.form("intervention"):
        col1, col2 = st.columns(2)
        with col1:
            date_i = st.date_input("Date", datetime.now().date())
            techniciens = st.text_input("Technicien(s)")
            client = st.text_input("Client / Société")
            site = st.text_input("Site")
            localisation = st.text_input("Localisation")
            type_i = st.selectbox("Type d'intervention",
                                  ["Dépannage","Maintenance","Installation","Contrôle / mesure","Autre"])
            equipement = st.text_input("Équipement concerné")
            fibre_type = st.selectbox("Type de fibre", ["Monomode","Multimode","Inconnu / autre"])
        with col2:
            heure_debut = st.time_input("Heure de début")
            heure_fin = st.time_input("Heure de fin")
            probleme = st.text_area("Nature du problème / demande")
            diagnostic = st.text_area("Diagnostic effectué")
            distance = st.text_input("Distance du défaut (m)")
            p_avant = st.text_input("Puissance avant (dBm)")
            p_apres = st.text_input("Puissance après (dBm)")
            resultat = st.selectbox("Résultat",
                                    ["Service rétabli","Intervention terminée — conforme",
                                     "Intervention partielle","Défaut non résolu","À suivre"])

        travaux = st.text_area("Travaux réalisés")
        materiel = st.text_area("Matériel utilisé")
        recommandations = st.text_area("Recommandations")
        observations = st.text_area("Observations")

        photos = st.file_uploader("Photos / preuves (optionnel)",
                                  type=["jpg","jpeg","png","webp"], accept_multiple_files=True)

        submitted = st.form_submit_button("💾 Enregistrer l'intervention", type="primary")

    if submitted:
        data = [
            numero, str(date_i), techniciens, client, site, localisation, type_i,
            str(heure_debut), str(heure_fin), equipement, fibre_type, probleme,
            diagnostic, distance, p_avant, p_apres, travaux, materiel, resultat,
            recommandations, observations
        ]
        save_intervention(data)
        if photos:
            folder = UPLOADS / numero
            folder.mkdir(exist_ok=True)
            for photo in photos:
                (folder / photo.name).write_bytes(photo.getbuffer())
        st.success(f"Intervention {numero} enregistrée avec succès.")
        st.balloons()

elif menu == "Historique":
    st.header("📚 Historique complet")

    with conn() as c:
        if role in ["administrateur", "chef", "superviseur"]:
            rows = c.execute(
                "SELECT * FROM interventions ORDER BY id DESC"
            ).fetchall()
        else:
            rows = c.execute(
                """
                SELECT * FROM interventions
                WHERE created_by = ?
                ORDER BY id DESC
                """,
                (st.session_state.user_id,)
            ).fetchall()

    df = pd.DataFrame([dict(r) for r in rows])

    if df.empty:
        st.warning("Aucune intervention enregistrée.")
    else:
        search = st.text_input(
            "🔎 Rechercher par numéro, client, site, problème..."
        )

        view = df.copy()

        if search:
            mask = view.astype(str).apply(
                lambda col: col.str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False
                )
            )
            view = view[mask.any(axis=1)]

        st.dataframe(
            view[
                [
                    "numero",
                    "date_intervention",
                    "client",
                    "site",
                    "type_intervention",
                    "probleme",
                    "resultat",
                    "statut",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Exporter CSV",
            view.to_csv(index=False).encode("utf-8-sig"),
            "historique_interventions.csv",
            "text/csv",
        )

        st.divider()
        st.subheader("📄 Document PDF")

        numeros = view["numero"].tolist()

        if numeros:
            selected_numero = st.selectbox(
                "Sélectionner l'intervention",
                numeros,
            )

            selected = next(
                (row for row in rows if row["numero"] == selected_numero),
                None,
            )

            if selected:
                st.subheader("🔄 Workflow")

                if (
                    selected["created_by"] == st.session_state.user_id
                    and selected["statut"] == "Brouillon"
                ):
                    if st.button(
                        "📤 Soumettre",
                        use_container_width=True
                    ):
                        with conn() as c:
                            c.execute(
                                """
                                UPDATE interventions
                                SET statut = 'Soumise',
                                    soumise_le = ?
                                WHERE id = ?
                                """,
                                (
                                    datetime.now().isoformat(timespec="seconds"),
                                    selected["id"],
                                ),
                            )

                        st.success(
                            f"Intervention {selected_numero} soumise au Chef / Superviseur."
                        )
                        st.rerun()

                pdf_bytes = generate_pdf(selected)
                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "👁️ Visualiser le PDF",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state["show_pdf"] = True

                with col2:
                    st.download_button(
                        "⬇️ Télécharger le PDF",
                        pdf_bytes,
                        f"{selected_numero}.pdf",
                        "application/pdf",
                        use_container_width=True,
                    )

                if st.session_state.get("show_pdf", False):
                    st.markdown("### 👁️ Aperçu avant impression")
                    st.components.v1.html(
                        pdf_preview(pdf_bytes),
                        height=870,
                        scrolling=False,
                    )

                    st.info(
                        "💡 Pour imprimer, utilise le bouton d'impression "
                        "du lecteur PDF affiché ci-dessus."
                    )

elif menu == "Tableau de bord":
    st.header("📊 Tableau de bord")
    with conn() as c:
        total = c.execute("SELECT COUNT(*) n FROM interventions").fetchone()["n"]
        today = c.execute("SELECT COUNT(*) n FROM interventions WHERE date_intervention=?",
                          (str(datetime.now().date()),)).fetchone()["n"]
        sites = c.execute("SELECT COUNT(DISTINCT site) n FROM interventions WHERE site<>''").fetchone()["n"]
        unresolved = c.execute("""SELECT COUNT(*) n FROM interventions
                                  WHERE resultat IN ('Défaut non résolu','Intervention partielle','À suivre')""").fetchone()["n"]
    a,b,c,d = st.columns(4)
    a.metric("Total interventions", total)
    b.metric("Aujourd'hui", today)
    c.metric("Sites suivis", sites)
    d.metric("À suivre", unresolved)

    st.markdown("""
    ### Principe de traçabilité
    - **1 intervention = 1 numéro unique**
    - Les journées successives sont conservées dans le même historique.
    - Les mesures avant/après, travaux, matériel, résultat et observations sont archivés.
    - Les photos sont rangées par numéro d'intervention.
    - L'historique peut être exporté en CSV pour archivage.
    """)
elif menu == "Gestion des utilisateurs":
    st.header("👥 Gestion des utilisateurs")
    st.caption("Création et gestion des comptes utilisateurs")

    st.subheader("➕ Créer un utilisateur")

    with st.form("create_user_form"):
        nom = st.text_input("Nom complet")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")

        role = st.selectbox(
            "Rôle",
            [
                "administrateur",
                "chef",
                "technicien",
                "sous-traitant",
                "ingenieur",
            ],
            format_func=lambda x: {
                "administrateur": "👑 Administrateur",
                "chef": "👨‍💼 Chef / Superviseur",
                "technicien": "👨‍🔧 Technicien",
                "sous-traitant": "🧰 Sous-traitant",
                "ingenieur": "👷 Ingénieur",
            }[x],
        )

        create = st.form_submit_button("Créer le compte")

        if create:
            if not nom or not username or not password:
                st.error("Tous les champs sont obligatoires.")
            elif len(password) < 8:
                st.error("Le mot de passe doit contenir au moins 8 caractères.")
            else:
                try:
                    with conn() as c:
                        c.execute(
                            """
                            INSERT INTO users
                            (username, password_hash, nom, role, actif, cree_le)
                            VALUES (?, ?, ?, ?, 1, ?)
                            """,
                            (
                                username,
                                hash_password(password),
                                nom,
                                role,
                                datetime.now().isoformat(timespec="seconds"),
                            ),
                        )

                    st.success(f"Utilisateur {username} créé avec succès.")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error("Ce nom d'utilisateur existe déjà.")

    st.divider()

    st.subheader("📋 Utilisateurs existants")

    with conn() as c:
        users = c.execute(
            """
            SELECT id, username, nom, role, actif, cree_le
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()

    if users:
        users_df = pd.DataFrame([dict(u) for u in users])
        st.dataframe(users_df, use_container_width=True)
    else:
        st.info("Aucun utilisateur enregistré.")
