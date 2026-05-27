import requests
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard ILD", layout="wide")
st.title("ILD Benchmark — Comparativa de Modelos")

API_URL = "http://localhost:8001/api/recommend"
MODELS = ["self_query", "hybrid", "multi_query", "combined", "parent"]
COLORS = {"self_query": "#378ADD", "hybrid": "#1D9E75", "multi_query": "#D85A30", "combined": "#7F77DD"}

test_cases = [
    "sci-fi movies directed by Ridley Scott released in the 1980s",
    "action movies directed by Quentin Tarantino with tomatometer above 90",
    "movies directed by Christopher Nolan with a runtime over 140 minutes",
    "black and white samurai movies from the 1950s",
    "romantic comedies starring Meg Ryan from the 1990s",
    "stop-motion animation movies directed by Wes Anderson",
    "slasher horror films released strictly between 1980 and 1984",
]

# --- funciones de cálculo (igual que antes) ---
def calc_jaccard(l1, l2):
    s1, s2 = set(l1), set(l2)
    if not s1 and not s2: return 0.0
    return 1.0 - len(s1 & s2) / len(s1 | s2)

def get_distance(m1, m2):
    g1 = [g.strip() for g in m1.get("genres","").split(",") if g.strip()]
    g2 = [g.strip() for g in m2.get("genres","").split(",") if g.strip()]
    d_gen = calc_jaccard(g1, g2)
    d_dir = calc_jaccard(m1.get("directors",[]), m2.get("directors",[]))
    try:
        y1, y2 = int(m1.get("year",0)), int(m2.get("year",0))
        d_year = min(abs(y1-y2)/40.0, 1.0) if y1 and y2 else 1.0
    except:
        d_year = 1.0
    return d_gen*0.5 + d_dir*0.3 + d_year*0.2

def compute_ild(movies):
    n = len(movies)
    if n <= 1: return 0.0
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                mat[i][j] = get_distance(movies[i], movies[j])
    return float(np.mean(mat[np.triu_indices(n, k=1)]))

# --- UI ---
if st.button("Ejecutar Benchmark", type="primary"):
    pb = st.progress(0)
    rows = []
    total = len(test_cases) * len(MODELS)
    step = 0

    for prompt in test_cases:
        for model in MODELS:
            try:
                res = requests.post(API_URL, json={"query": prompt, "model": model, "max_results": 10})
                movies = res.json().get("results", [])
                ild = compute_ild(movies)
            except:
                ild = 0.0

            rows.append({"Prompt": prompt[:40]+"...", "Modelo": model, "ILD": round(ild, 4)})
            step += 1
            pb.progress(step / total)

    df = pd.DataFrame(rows)
    st.success("Benchmark completado.")

    # --- Tarjetas resumen ---
    cols = st.columns(len(MODELS))
    for col, model in zip(cols, MODELS):
        avg = df[df.Modelo == model]["ILD"].mean()
        col.metric(model.replace("_"," "), f"{avg:.3f}", "avg ILD")

    st.markdown("---")

    # --- Gráfica agrupada ---
    fig_bar = px.bar(
        df, x="Prompt", y="ILD", color="Modelo",
        barmode="group",
        color_discrete_map=COLORS,
        title="ILD por consulta y modelo",
        height=400,
    )
    fig_bar.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Radar / polar ---
    avg_df = df.groupby("Modelo")["ILD"].mean().reset_index()
    fig_polar = px.line_polar(
        avg_df, r="ILD", theta="Modelo",
        line_close=True,
        color_discrete_sequence=list(COLORS.values()),
        title="Media ILD por modelo",
    )
    fig_polar.update_traces(fill="toself")
    st.plotly_chart(fig_polar, use_container_width=True)

    with st.expander("Ver datos completos"):
        st.dataframe(df, use_container_width=True)