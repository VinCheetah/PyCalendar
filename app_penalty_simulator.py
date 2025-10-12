"""
Simulateur de Pénalités Horaires - Version Simplifiée

Outil pédagogique pour comprendre comment la formule de pénalité
réagit selon les différents scénarios possibles.
Utilise les données réelles de la configuration pour les horaires.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import List, Tuple, Optional, Dict
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from data.data_source import DataSource


# Configuration de la page
st.set_page_config(
    page_title="Simulateur de Pénalités",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1rem !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem !important;
        font-weight: bold !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 1rem;
        border-bottom: 3px solid #1f77b4;
    }
    h2 {
        color: #2c3e50;
        margin-top: 2rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #ecf0f1;
    }
    h3 {
        color: #34495e;
        margin-top: 1.5rem;
    }
    .scenario-box {
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .scenario-after {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        color: white;
    }
    .scenario-before-1 {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        color: white;
    }
    .scenario-before-2 {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
    }
    .formula-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def format_time(minutes: int) -> str:
    """Convertit des minutes depuis minuit en format HH:MM."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}h{mins:02d}"


def calculate_penalty(
    horaire_prefere_min: int,
    horaire_match_min: int,
    tolerance: float,
    diviseur: float,
    mult_apres: float,
    mult_avant_1: float,
    mult_avant_2: float,
    nb_equipes_avant: int
) -> Tuple[float, str, bool]:
    """
    Calcule la pénalité pour un horaire donné.
    
    Returns:
        (penalty, explanation, in_tolerance)
    """
    distance = abs(horaire_match_min - horaire_prefere_min)
    
    # Dans la tolérance
    if distance <= tolerance:
        return 0.0, f"✅ Dans la tolérance (±{int(tolerance)} min)", True
    
    # Hors tolérance
    is_before = horaire_match_min < horaire_prefere_min
    penalite_base = (distance / diviseur) ** 2
    
    if nb_equipes_avant == 0:
        # APRÈS
        penalty = mult_apres * penalite_base
        explanation = f"🟢 APRÈS horaire préféré (mult. {mult_apres}x)"
    elif nb_equipes_avant == 1:
        # 1 AVANT
        penalty = mult_avant_1 * penalite_base
        explanation = f"🟠 AVANT pour 1 équipe (mult. {mult_avant_1}x)"
    else:
        # 2 AVANT
        penalty = mult_avant_2 * penalite_base
        explanation = f"🔴 AVANT pour 2 équipes (mult. {mult_avant_2}x)"
    
    return penalty, explanation, False


def create_penalty_curve(
    horaire_prefere: int,
    tolerance: float,
    diviseur: float,
    mult_apres: float,
    mult_avant: float,
    max_distance: int = 240
):
    """Crée une courbe de pénalité autour d'un horaire préféré."""
    
    # Créer les points de la courbe
    distances = list(range(-max_distance, max_distance + 1, 5))
    horaires = [horaire_prefere + d for d in distances]
    
    penalties_apres = []
    penalties_avant = []
    
    for horaire in horaires:
        dist = abs(horaire - horaire_prefere)
        
        if dist <= tolerance:
            penalties_apres.append(0)
            penalties_avant.append(0)
        else:
            base = (dist / diviseur) ** 2
            
            if horaire > horaire_prefere:
                # APRÈS
                penalties_apres.append(mult_apres * base)
                penalties_avant.append(None)
            else:
                # AVANT
                penalties_apres.append(None)
                penalties_avant.append(mult_avant * base)
    
    # Créer le graphique avec valeurs numériques pour l'axe X
    fig = go.Figure()
    
    # Zone de tolérance (utilise les valeurs numériques)
    fig.add_vrect(
        x0=horaire_prefere - tolerance,
        x1=horaire_prefere + tolerance,
        fillcolor="lightgreen",
        opacity=0.2,
        layer="below",
        line_width=0,
        annotation_text="Zone de tolérance",
        annotation_position="top left"
    )
    
    # Ligne APRÈS (utilise les valeurs numériques)
    fig.add_trace(go.Scatter(
        x=horaires,
        y=penalties_apres,
        mode='lines',
        name='APRÈS horaire (préférable)',
        line=dict(color='#2ecc71', width=3),
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.1)',
        hovertemplate='%{x|%Hh%M}: %{y:.2f}<extra></extra>'
    ))
    
    # Ligne AVANT (utilise les valeurs numériques)
    fig.add_trace(go.Scatter(
        x=horaires,
        y=penalties_avant,
        mode='lines',
        name='AVANT horaire (problématique)',
        line=dict(color='#e74c3c', width=3),
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.1)',
        hovertemplate='%{x|%Hh%M}: %{y:.2f}<extra></extra>'
    ))
    
    # Ligne verticale à l'horaire préféré (utilise la valeur numérique)
    fig.add_vline(
        x=horaire_prefere,
        line_dash="dash",
        line_color="blue",
        annotation_text="Horaire préféré",
        annotation_position="top"
    )
    
    fig.update_layout(
        title="Évolution de la Pénalité Autour de l'Horaire Préféré",
        xaxis_title="Horaire du Match",
        yaxis_title="Pénalité",
        height=500,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Formater l'axe X pour afficher les heures
    # Créer des ticks toutes les 30 minutes sur une plage visible
    tick_vals = list(range(int(horaire_prefere - max_distance), int(horaire_prefere + max_distance + 1), 60))
    tick_texts = [format_time(v) for v in tick_vals]
    
    fig.update_xaxes(
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_texts,
        tickangle=-45
    )
    
    return fig


@st.cache_resource
def load_real_data(config_path: str) -> Optional[Tuple[Config, DataSource, List[str], List[str]]]:
    """Charge les données réelles depuis la configuration."""
    try:
        config = Config.from_yaml(config_path)
        source = DataSource(config.fichier_donnees)
        
        # Extraire tous les horaires préférés uniques
        equipes = source.charger_equipes()
        horaires_preferes = set()
        for equipe in equipes:
            if equipe.horaires_preferes:
                horaires_preferes.update(equipe.horaires_preferes)
        
        # Extraire tous les horaires de gymnases uniques
        gymnases = source.charger_gymnases()
        horaires_gymnases = set()
        for gymnase in gymnases:
            if gymnase.horaires_disponibles:
                horaires_gymnases.update(gymnase.horaires_disponibles)
        
        # Trier et formater
        horaires_preferes = sorted(list(horaires_preferes))
        horaires_gymnases = sorted(list(horaires_gymnases))
        
        return config, source, horaires_preferes, horaires_gymnases
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return None


def parse_horaire(horaire: str) -> int:
    """Convertit un horaire en minutes depuis minuit."""
    try:
        horaire = horaire.strip().upper().replace('H', ':')
        if ':' not in horaire:
            horaire += ':00'
        parts = horaire.split(':')
        heures = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return heures * 60 + minutes
    except (ValueError, IndexError):
        return 14 * 60  # 14h par défaut


def find_best_match_horaire(
    horaires_eq1: List[str],
    horaires_eq2: List[str],
    horaires_disponibles: List[str],
    tolerance: float,
    diviseur: float,
    mult_apres: float,
    mult_avant_1: float,
    mult_avant_2: float
) -> List[Dict]:
    """
    Trouve les meilleurs horaires de match pour deux équipes.
    
    Returns:
        Liste de dictionnaires avec horaire_match, penalty, details
    """
    results = []
    
    # Convertir en minutes
    horaires_eq1_min = [parse_horaire(h) for h in horaires_eq1]
    horaires_eq2_min = [parse_horaire(h) for h in horaires_eq2]
    horaires_dispo_min = [parse_horaire(h) for h in horaires_disponibles]
    
    # Tester chaque horaire disponible
    for horaire_match_min in horaires_dispo_min:
        # Trouver les horaires préférés les plus proches pour chaque équipe
        dist_eq1 = [abs(horaire_match_min - h) for h in horaires_eq1_min]
        dist_eq2 = [abs(horaire_match_min - h) for h in horaires_eq2_min]
        
        min_dist_eq1 = min(dist_eq1)
        min_dist_eq2 = min(dist_eq2)
        
        closest_pref_eq1 = horaires_eq1_min[dist_eq1.index(min_dist_eq1)]
        closest_pref_eq2 = horaires_eq2_min[dist_eq2.index(min_dist_eq2)]
        
        # Déterminer si avant ou après
        is_before_eq1 = horaire_match_min < closest_pref_eq1
        is_before_eq2 = horaire_match_min < closest_pref_eq2
        
        # Vérifier la tolérance
        in_tolerance_eq1 = min_dist_eq1 <= tolerance
        in_tolerance_eq2 = min_dist_eq2 <= tolerance
        
        # CORRECTION : Compter uniquement les équipes HORS tolérance qui jouent AVANT
        nb_before_hors_tolerance = 0
        if not in_tolerance_eq1 and is_before_eq1:
            nb_before_hors_tolerance += 1
        if not in_tolerance_eq2 and is_before_eq2:
            nb_before_hors_tolerance += 1
        
        # Déterminer le multiplicateur (basé uniquement sur les équipes hors tolérance)
        if nb_before_hors_tolerance == 2:
            multiplicateur = mult_avant_2
        elif nb_before_hors_tolerance == 1:
            multiplicateur = mult_avant_1
        else:
            multiplicateur = mult_apres
        
        # Calculer pénalité avec le bon multiplicateur
        penalty_total = 0
        
        if not in_tolerance_eq1:
            base_eq1 = (min_dist_eq1 / diviseur) ** 2
            penalty_total += multiplicateur * base_eq1
        
        if not in_tolerance_eq2:
            base_eq2 = (min_dist_eq2 / diviseur) ** 2
            penalty_total += multiplicateur * base_eq2
        
        # Détails
        if in_tolerance_eq1 and in_tolerance_eq2:
            details = "✅ Dans la tolérance pour les 2 équipes"
        elif nb_before_hors_tolerance == 2:
            details = f"🔴 AVANT les 2 équipes (hors tolérance) - mult. {multiplicateur}x"
        elif nb_before_hors_tolerance == 1:
            details = f"🟠 AVANT 1 équipe (hors tolérance) - mult. {multiplicateur}x"
        else:
            details = f"🟢 APRÈS horaires - mult. {multiplicateur}x"
        
        results.append({
            'horaire_match': format_time(horaire_match_min),
            'horaire_match_min': horaire_match_min,
            'penalty': penalty_total,
            'dist_eq1': min_dist_eq1,
            'dist_eq2': min_dist_eq2,
            'in_tol_eq1': in_tolerance_eq1,
            'in_tol_eq2': in_tolerance_eq2,
            'before_eq1': is_before_eq1,
            'before_eq2': is_before_eq2,
            'details': details
        })
    
    # Trier par pénalité
    results.sort(key=lambda x: x['penalty'])
    
    return results


def main():
    # Titre
    st.markdown("# 🎲 Simulateur de Pénalités Horaires")
    st.markdown("Analysez les paramètres de pénalité avec vos données réelles")
    
    # Sidebar - Configuration OBLIGATOIRE
    with st.sidebar:
        st.markdown("## 📁 Configuration")
        
        config_path = st.text_input(
            "Chemin de configuration",
            value="configs/config_hand.yaml",
            help="Fichier YAML de configuration"
        )
        
        if st.button("🔄 Charger la configuration", type="primary", use_container_width=True):
            real_data = load_real_data(config_path)
            if real_data:
                st.session_state.real_data = real_data
                st.success("✅ Configuration chargée !")
                st.rerun()
        
        # Vérifier que la configuration est chargée
        if 'real_data' not in st.session_state:
            st.warning("⚠️ **Configuration requise**")
            st.info("""
            👆 Chargez une configuration pour :
            - Utiliser les horaires préférés des équipes
            - Utiliser les horaires des gymnases
            - Charger vos paramètres de pénalité
            """)
            st.stop()
        
        # Récupérer les données
        config, source, horaires_pref, horaires_gym = st.session_state.real_data
        
        st.success(f"✅ Configuré : {config_path.split('/')[-1]}")
        st.metric("Horaires préférés", len(horaires_pref))
        st.metric("Horaires gymnases", len(horaires_gym))
        
        st.markdown("---")
        st.markdown("## ⚙️ Paramètres de Pénalité")
        st.caption("💡 Valeurs issues de votre configuration")
        
        # Tolérance (depuis config)
        st.markdown("### 📏 Tolérance")
        tolerance = st.slider(
            "Tolérance (minutes)",
            min_value=0,
            max_value=120,
            value=int(config.penalite_horaire_tolerance),
            step=5,
            help="Zone sans pénalité autour de l'horaire préféré"
        )
        
        # Diviseur (depuis config)
        st.markdown("### 📐 Diviseur")
        diviseur = st.slider(
            "Diviseur de distance",
            min_value=10,
            max_value=120,
            value=int(config.penalite_horaire_diviseur),
            step=5,
            help="Plus grand = pénalité moins forte"
        )
        
        # Multiplicateurs (depuis config)
        st.markdown("### 📊 Multiplicateurs")
        
        mult_apres = st.number_input(
            "APRÈS (préférable)",
            min_value=0.1,
            max_value=100.0,
            value=float(config.penalite_apres_horaire_min),
            step=1.0,
            help="Match après l'horaire préféré"
        )
        
        mult_avant_1 = st.number_input(
            "AVANT (1 équipe)",
            min_value=1.0,
            max_value=500.0,
            value=float(config.penalite_avant_horaire_min),
            step=10.0,
            help="1 équipe joue avant son horaire"
        )
        
        mult_avant_2 = st.number_input(
            "AVANT (2 équipes)",
            min_value=1.0,
            max_value=1000.0,
            value=float(config.penalite_avant_horaire_min_deux),
            step=50.0,
            help="2 équipes jouent avant leur horaire"
        )
        
        st.markdown("---")
        
        # Horaire de référence pour simulations simples
        st.markdown("### 🎯 Horaire de Référence")
        st.caption("Pour les onglets Courbe et Simulateur")
        heure_pref = st.slider("Heure", 8, 22, 14, key="heure_pref")
        minute_pref = st.select_slider("Minutes", [0, 15, 30, 45], value=0, key="min_pref")
        horaire_prefere_min = heure_pref * 60 + minute_pref
        st.info(f"⏰ {format_time(horaire_prefere_min)}")
    
    # Corps principal - Onglets
    # Créer les onglets (configuration toujours chargée)
    tab_search, tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Trouver Meilleur Horaire",
        "📊 Courbe Globale",
        "🎯 Simulateur",
        "📈 Comparaison Scénarios",
        "📚 Documentation"
    ])
    
    # TAB SEARCH: Recherche d'horaires optimaux
    with tab_search:
        st.markdown("## 🔍 Trouver le Meilleur Horaire de Match")
        st.markdown("Sélectionnez les horaires préférés de deux équipes et trouvez les meilleurs créneaux de match")
        
        # Récupérer les données depuis session_state
        config, source, horaires_pref, horaires_gym = st.session_state.real_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏐 Équipe 1 - Horaires Préférés")
            horaires_eq1 = st.multiselect(
                "Sélectionnez un ou plusieurs horaires",
                options=horaires_pref,
                default=[horaires_pref[0]] if horaires_pref else [],
                key="eq1_pref"
            )
            
            if horaires_eq1:
                st.success(f"✅ {len(horaires_eq1)} horaire(s) sélectionné(s)")
        
        with col2:
            st.markdown("### 🏐 Équipe 2 - Horaires Préférés")
            horaires_eq2 = st.multiselect(
                "Sélectionnez un ou plusieurs horaires",
                options=horaires_pref,
                default=[horaires_pref[1]] if len(horaires_pref) > 1 else [],
                key="eq2_pref"
            )
            
            if horaires_eq2:
                st.success(f"✅ {len(horaires_eq2)} horaire(s) sélectionné(s)")
        
        st.markdown("---")
        
        if horaires_eq1 and horaires_eq2:
            # Rechercher les meilleurs horaires
            results = find_best_match_horaire(
                horaires_eq1,
                horaires_eq2,
                horaires_gym,
                tolerance,
                diviseur,
                mult_apres,
                mult_avant_1,
                mult_avant_2
            )
            
            if results:
                # Meilleur horaire
                best = results[0]
                
                st.markdown("### 🏆 Meilleur Créneau")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Horaire Optimal",
                        best['horaire_match'],
                        delta="Pénalité minimale"
                    )
                
                with col2:
                    st.metric(
                        "Pénalité Totale",
                        f"{best['penalty']:.2f}",
                        delta=None
                    )
                
                with col3:
                    if best['penalty'] < 1:
                        color = "🟢"
                        status = "Excellent"
                    elif best['penalty'] < 10:
                        color = "🟡"
                        status = "Bon"
                    elif best['penalty'] < 50:
                        color = "🟠"
                        status = "Acceptable"
                    else:
                        color = "🔴"
                        status = "Problématique"
                    
                    st.metric(
                        "Évaluation",
                        f"{color} {status}",
                        delta=None
                    )
                
                # Détails du meilleur créneau
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 1.5rem; border-radius: 1rem; color: white; margin: 1rem 0;">
                    <h3 style="margin:0;">⏰ {best['horaire_match']}</h3>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                        Équipe 1: {int(best['dist_eq1'])} min {"✅" if best['in_tol_eq1'] else ("⚠️ AVANT" if best['before_eq1'] else "ℹ️ APRÈS")}
                        • 
                        Équipe 2: {int(best['dist_eq2'])} min {"✅" if best['in_tol_eq2'] else ("⚠️ AVANT" if best['before_eq2'] else "ℹ️ APRÈS")}
                    </p>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{best['details']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Comparaison avec alternatives
                if len(results) > 1:
                    st.markdown("### 🥈 Top 5 des Alternatives")
                    
                    df_results = pd.DataFrame(results[:5])
                    df_display = pd.DataFrame({
                        'Rang': range(1, min(6, len(results) + 1)),
                        'Horaire': [r['horaire_match'] for r in results[:5]],
                        'Pénalité': [f"{r['penalty']:.2f}" for r in results[:5]],
                        'Dist. Eq1': [f"{int(r['dist_eq1'])} min" for r in results[:5]],
                        'Dist. Eq2': [f"{int(r['dist_eq2'])} min" for r in results[:5]],
                        'Détails': [r['details'] for r in results[:5]]
                    })
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Graphique de distribution
                    st.markdown("### 📊 Distribution des Pénalités")
                    
                    fig_dist = go.Figure()
                    
                    # Tous les créneaux
                    fig_dist.add_trace(go.Bar(
                        x=[r['horaire_match'] for r in results],
                        y=[r['penalty'] for r in results],
                        marker_color=['gold' if i == 0 else 'lightblue' for i in range(len(results))],
                        name='Pénalités',
                        hovertemplate='%{x}: %{y:.2f}<extra></extra>'
                    ))
                    
                    fig_dist.update_layout(
                        title="Pénalités de tous les créneaux disponibles",
                        xaxis_title="Horaire du Match",
                        yaxis_title="Pénalité",
                        height=400,
                        showlegend=False
                    )
                    
                    fig_dist.update_xaxes(tickangle=-45)
                    
                    st.plotly_chart(fig_dist, use_container_width=True)
                    
                    # Analyse comparative
                    st.markdown("### 📊 Analyse")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        nb_zero = sum(1 for r in results if r['penalty'] < 0.01)
                        st.metric("Créneaux parfaits", nb_zero, "Pénalité = 0")
                    
                    with col2:
                        nb_acceptable = sum(1 for r in results if r['penalty'] < 10)
                        pct = (nb_acceptable / len(results)) * 100
                        st.metric("Créneaux acceptables", f"{pct:.0f}%", "Pénalité < 10")
                    
                    with col3:
                        if len(results) > 1:
                            diff = results[1]['penalty'] - results[0]['penalty']
                            st.metric("Écart avec 2ème", f"{diff:.2f}", 
                                     "Sensibilité" if diff < 5 else "Choix clair")
            else:
                st.warning("Aucun créneau disponible trouvé")
        else:
            st.info("👆 Sélectionnez les horaires préférés des deux équipes pour commencer")
    
    # TAB 1: Courbe globale
    with tab1:
        st.markdown("## 📊 Visualisation Globale de la Pénalité")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Zone de tolérance",
                f"±{int(tolerance)} min",
                "Pénalité = 0"
            )
        
        with col2:
            st.metric(
                "Diviseur",
                f"÷ {int(diviseur)}",
                "Amortit la distance"
            )
        
        with col3:
            ratio = mult_avant_2 / mult_apres if mult_apres > 0 else 0
            st.metric(
                "Ratio AVANT/APRÈS",
                f"{ratio:.0f}x",
                "Plus élevé = AVANT très pénalisé"
            )
        
        st.markdown("---")
        
        # Graphique pour 1 équipe avant
        st.markdown("### Scénario : 1 Équipe avec Horaire Préféré")
        fig1 = create_penalty_curve(
            horaire_prefere_min,
            tolerance,
            diviseur,
            mult_apres,
            mult_avant_1,
            max_distance=180
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("""
        <div class="info-box">
        📖 <strong>Lecture du graphique :</strong><br>
        • La zone verte claire = tolérance (pénalité nulle)<br>
        • Ligne verte = match APRÈS l'horaire préféré (acceptable)<br>
        • Ligne rouge = match AVANT l'horaire préféré (problématique)<br>
        • Plus on s'éloigne, plus la pénalité augmente (au carré !)<br>
        </div>
        """, unsafe_allow_html=True)
    
    # TAB 2: Simulateur
    with tab2:
        st.markdown("## 🎯 Simulateur de Match")
        st.markdown("Testez différents horaires de match et voyez la pénalité résultante")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### ⚙️ Configuration du Match")
            
            # Horaire du match
            heure_match = st.slider("Heure du match", 8, 22, 16, key="heure_match")
            minute_match = st.select_slider("Minutes", [0, 15, 30, 45], value=0, key="min_match")
            horaire_match_min = heure_match * 60 + minute_match
            
            st.info(f"⏰ Horaire du match : **{format_time(horaire_match_min)}**")
            
            # Nombre d'équipes avant
            nb_equipes_avant = st.radio(
                "Scénario",
                [0, 1, 2],
                format_func=lambda x: {
                    0: "🟢 APRÈS les horaires préférés",
                    1: "🟠 AVANT pour 1 équipe",
                    2: "🔴 AVANT pour 2 équipes"
                }[x],
                help="Simule combien d'équipes jouent avant leur horaire préféré"
            )
        
        with col2:
            st.markdown("### 📊 Résultats")
            
            # Calcul
            distance = abs(horaire_match_min - horaire_prefere_min)
            
            if nb_equipes_avant == 0:
                mult = mult_apres
            elif nb_equipes_avant == 1:
                mult = mult_avant_1
            else:
                mult = mult_avant_2
            
            penalty, explanation, in_tolerance = calculate_penalty(
                horaire_prefere_min,
                horaire_match_min,
                tolerance,
                diviseur,
                mult_apres,
                mult_avant_1,
                mult_avant_2,
                nb_equipes_avant
            )
            
            # Affichage résultats
            st.metric("Distance", f"{distance} min")
            
            if in_tolerance:
                st.success(f"✅ **Pénalité : 0.00**\n\n{explanation}")
            else:
                penalite_base = (distance / diviseur) ** 2
                
                st.error(f"**Pénalité totale : {penalty:.2f}**")
                
                st.markdown(f"""
                <div class="formula-box">
                <strong>Calcul détaillé :</strong><br><br>
                1️⃣ Distance = {distance} min<br>
                2️⃣ Pénalité de base = ({distance} / {diviseur})² = {penalite_base:.4f}<br>
                3️⃣ Multiplicateur = {mult}x<br>
                4️⃣ <strong>Pénalité finale = {mult} × {penalite_base:.4f} = {penalty:.2f}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                st.info(explanation)
        
        # Graphique avec point actuel
        st.markdown("---")
        st.markdown("### 📈 Position sur la Courbe")
        
        fig_sim = create_penalty_curve(
            horaire_prefere_min,
            tolerance,
            diviseur,
            mult_apres,
            mult_avant_1 if nb_equipes_avant == 1 else mult_avant_2,
            max_distance=180
        )
        
        # Ajouter le point actuel (utiliser valeur numérique)
        fig_sim.add_trace(go.Scatter(
            x=[horaire_match_min],
            y=[penalty],
            mode='markers',
            marker=dict(size=20, color='yellow', line=dict(width=2, color='black')),
            name='Match simulé',
            showlegend=True,
            hovertemplate='%{x|%Hh%M}: %{y:.2f}<extra></extra>'
        ))
        
        st.plotly_chart(fig_sim, use_container_width=True)
    
    # TAB 3: Comparaison scénarios
    with tab3:
        st.markdown("## 📈 Comparaison des 3 Scénarios")
        st.markdown("Voyez comment la pénalité évolue selon le scénario")
        
        # Sélection de l'horaire de test
        col1, col2 = st.columns(2)
        
        with col1:
            heure_test = st.slider("Heure de test", 8, 22, 16, key="heure_test")
            minute_test = st.select_slider("Minutes", [0, 15, 30, 45], value=0, key="min_test")
        
        horaire_test_min = heure_test * 60 + minute_test
        distance_test = abs(horaire_test_min - horaire_prefere_min)
        
        with col2:
            st.info(f"⏰ Horaire testé : **{format_time(horaire_test_min)}**")
            st.info(f"📏 Distance : **{distance_test} min**")
        
        st.markdown("---")
        
        # Calcul pour les 3 scénarios
        scenarios = []
        
        for nb_avant, label, color, emoji in [
            (0, "APRÈS horaires", "scenario-after", "🟢"),
            (1, "AVANT (1 équipe)", "scenario-before-1", "🟠"),
            (2, "AVANT (2 équipes)", "scenario-before-2", "🔴")
        ]:
            penalty, explanation, in_tolerance = calculate_penalty(
                horaire_prefere_min,
                horaire_test_min,
                tolerance,
                diviseur,
                mult_apres,
                mult_avant_1,
                mult_avant_2,
                nb_avant
            )
            
            scenarios.append({
                'label': label,
                'emoji': emoji,
                'penalty': penalty,
                'explanation': explanation,
                'in_tolerance': in_tolerance,
                'color': color
            })
        
        # Affichage
        col1, col2, col3 = st.columns(3)
        
        for col, scenario in zip([col1, col2, col3], scenarios):
            with col:
                st.markdown(f"""
                <div class="scenario-box {scenario['color']}">
                    <h3 style="margin:0; color:white;">{scenario['emoji']} {scenario['label']}</h3>
                    <p style="font-size: 2.5rem; margin: 1rem 0; font-weight: bold;">
                        {scenario['penalty']:.2f}
                    </p>
                    <p style="margin:0; opacity:0.9;">
                        {scenario['explanation']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Comparaison
        if not scenarios[0]['in_tolerance']:
            st.markdown("---")
            st.markdown("### 🔍 Analyse Comparative")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ratio_1 = scenarios[1]['penalty'] / scenarios[0]['penalty'] if scenarios[0]['penalty'] > 0 else 0
                st.metric(
                    "AVANT (1 eq) vs APRÈS",
                    f"{ratio_1:.1f}x plus pénalisé",
                    delta=f"+{scenarios[1]['penalty'] - scenarios[0]['penalty']:.2f}",
                    delta_color="inverse"
                )
            
            with col2:
                ratio_2 = scenarios[2]['penalty'] / scenarios[0]['penalty'] if scenarios[0]['penalty'] > 0 else 0
                st.metric(
                    "AVANT (2 eq) vs APRÈS",
                    f"{ratio_2:.1f}x plus pénalisé",
                    delta=f"+{scenarios[2]['penalty'] - scenarios[0]['penalty']:.2f}",
                    delta_color="inverse"
                )
        
        # Graphique comparatif des 3 courbes
        st.markdown("---")
        st.markdown("### 📊 Courbes Comparatives")
        
        distances = list(range(-180, 181, 5))
        horaires_comp = [horaire_prefere_min + d for d in distances]
        
        # Calculer pour chaque scénario
        data_scenarios = []
        
        for scenario_id, (nb_avant, label, color_name) in enumerate([
            (0, "APRÈS", "#2ecc71"),
            (1, "AVANT (1 eq)", "#f39c12"),
            (2, "AVANT (2 eq)", "#e74c3c")
        ]):
            penalties = []
            
            for h in horaires_comp:
                p, _, _ = calculate_penalty(
                    horaire_prefere_min, h, tolerance, diviseur,
                    mult_apres, mult_avant_1, mult_avant_2, nb_avant
                )
                penalties.append(p)
            
            data_scenarios.append({
                'horaires': horaires_comp,  # Garder les valeurs numériques
                'penalties': penalties,
                'label': label,
                'color': color_name
            })
        
        fig_comp = go.Figure()
        
        for scenario in data_scenarios:
            fig_comp.add_trace(go.Scatter(
                x=scenario['horaires'],
                y=scenario['penalties'],
                mode='lines',
                name=scenario['label'],
                line=dict(color=scenario['color'], width=3),
                hovertemplate='%{x|%Hh%M}: %{y:.2f}<extra></extra>'
            ))
        
        # Point de test
        test_penalties = [s['penalty'] for s in scenarios]
        fig_comp.add_trace(go.Scatter(
            x=[horaire_test_min] * 3,  # Utiliser la valeur numérique
            y=test_penalties,
            mode='markers',
            marker=dict(size=15, color='yellow', line=dict(width=2, color='black')),
            name='Horaire testé',
            showlegend=True,
            hovertemplate='%{x|%Hh%M}: %{y:.2f}<extra></extra>'
        ))
        
        fig_comp.update_layout(
            title="Comparaison des 3 Scénarios",
            xaxis_title="Horaire du Match",
            yaxis_title="Pénalité",
            height=500,
            hovermode='x unified'
        )
        
        # Formater l'axe X
        tick_vals_comp = list(range(int(horaire_prefere_min - 180), int(horaire_prefere_min + 181), 60))
        tick_texts_comp = [format_time(v) for v in tick_vals_comp]
        
        fig_comp.update_xaxes(
            tickmode='array',
            tickvals=tick_vals_comp,
            ticktext=tick_texts_comp,
            tickangle=-45
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
    
    # TAB 4: Documentation
    with tab4:
        st.markdown("## 📚 Documentation de la Formule")
        
        st.markdown("""
        ### 🎯 Formule de Pénalité
        
        La pénalité est calculée en plusieurs étapes :
        """)
        
        st.markdown("""
        <div class="formula-box">
        <strong>Étape 1 : Calcul de la distance</strong><br>
        <code>distance = |horaire_match - horaire_préféré|</code><br><br>
        
        <strong>Étape 2 : Vérification de la tolérance</strong><br>
        <code>Si distance ≤ tolérance → pénalité = 0</code><br><br>
        
        <strong>Étape 3 : Calcul de la pénalité de base</strong><br>
        <code>pénalité_base = (distance / diviseur)²</code><br>
        ⚠️ Note : Élévation au carré = pénalité croît rapidement !<br><br>
        
        <strong>Étape 4 : Application du multiplicateur</strong><br>
        <code>Si match APRÈS les horaires → mult_après × pénalité_base</code><br>
        <code>Si 1 équipe AVANT → mult_avant_1 × pénalité_base</code><br>
        <code>Si 2 équipes AVANT → mult_avant_2 × pénalité_base</code><br>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### 💡 Comprendre les Paramètres")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📏 Tolérance
            
            **Rôle** : Zone de confort sans pénalité
            
            **Impact** :
            - ⬆️ Grande tolérance (60+ min) : Beaucoup de créneaux acceptables
            - ⬇️ Petite tolérance (15 min) : Seulement les créneaux proches sont OK
            
            **Conseil** : 30 min = bon équilibre
            """)
            
            st.markdown("""
            #### 📐 Diviseur
            
            **Rôle** : Contrôle la "sensibilité" à la distance
            
            **Impact** :
            - ⬆️ Grand diviseur (90-120) : Pénalités plus douces
            - ⬇️ Petit diviseur (30-45) : Pénalités plus sévères
            
            **Exemple** : 
            - Diviseur = 60 → 60 min d'écart = pénalité_base de 1
            - Diviseur = 30 → 60 min d'écart = pénalité_base de 4
            """)
        
        with col2:
            st.markdown("""
            #### 📊 Multiplicateur APRÈS
            
            **Rôle** : Pénalité quand match après l'horaire préféré
            
            **Impact** :
            - ⬇️ Faible (5-10) : Situation acceptable
            - ⬆️ Élevé (20+) : Même APRÈS est pénalisé
            
            **Logique** : Généralement on préfère jouer APRÈS que AVANT
            """)
            
            st.markdown("""
            #### 📊 Multiplicateurs AVANT
            
            **Rôle** : Pénalité forte pour situations problématiques
            
            **Impact** :
            - **AVANT 1 équipe** (100x) : Pénalité moyenne
            - **AVANT 2 équipes** (300x) : Pénalité très forte
            
            **Logique** : Obliger les équipes à jouer tôt est problématique
            
            **Rapport** : Généralement AVANT_2 = 3× AVANT_1
            """)
        
        st.markdown("---")
        
        st.markdown("### 🎓 Exemples Concrets")
        
        st.markdown(f"""
        Avec vos paramètres actuels :
        - Tolérance : **{int(tolerance)} min**
        - Diviseur : **{int(diviseur)}**
        - Multiplicateurs : APRÈS=**{mult_apres}**, AVANT(1)=**{mult_avant_1}**, AVANT(2)=**{mult_avant_2}**
        """)
        
        # Exemples
        examples = [
            (0, "Match exactement à l'horaire préféré"),
            (15, "15 minutes d'écart"),
            (30, "30 minutes d'écart"),
            (60, "1 heure d'écart"),
            (120, "2 heures d'écart")
        ]
        
        df_examples = []
        
        for dist, desc in examples:
            if dist <= tolerance:
                df_examples.append({
                    'Cas': desc,
                    'APRÈS': "0.00 ✅",
                    'AVANT (1 eq)': "0.00 ✅",
                    'AVANT (2 eq)': "0.00 ✅"
                })
            else:
                base = (dist / diviseur) ** 2
                p_apres = mult_apres * base
                p_avant1 = mult_avant_1 * base
                p_avant2 = mult_avant_2 * base
                
                df_examples.append({
                    'Cas': desc,
                    'APRÈS': f"{p_apres:.2f}",
                    'AVANT (1 eq)': f"{p_avant1:.2f}",
                    'AVANT (2 eq)': f"{p_avant2:.2f}"
                })
        
        df = pd.DataFrame(df_examples)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.markdown("""
        ### 🎯 Conseils d'Ajustement
        
        **Si vous avez trop de matchs AVANT les horaires préférés :**
        1. ⬆️ Augmentez les multiplicateurs AVANT
        2. ⬇️ Diminuez le multiplicateur APRÈS
        3. ⬆️ Augmentez la tolérance (si acceptable)
        
        **Si vous n'avez pas assez de créneaux acceptables :**
        1. ⬆️ Augmentez la tolérance
        2. ⬆️ Augmentez le diviseur
        3. ⬇️ Diminuez tous les multiplicateurs proportionnellement
        
        **Pour une optimisation équilibrée :**
        - Gardez un ratio AVANT_2 / AVANT_1 / APRÈS d'environ **30:10:1**
        - Tolérance entre 30-45 minutes
        - Diviseur autour de 60
        """)


if __name__ == "__main__":
    main()
