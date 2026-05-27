import time
import logging
import requests
import pandas as pd
import altair as alt
import streamlit as st
from typing import List, Dict, Set, Any

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
API_URL = "http://localhost:8001/api/recommend"
MODELS_TO_TEST = ["self_query", "hybrid", "multi_query", "combined", "parent"]
REQUEST_TIMEOUT = 210

TEST_QUERIES = [
    "a profound psychological thriller that leaves you questioning reality",
    "a movie that perfectly captures the feeling of profound loneliness in a big city",
    "a visually stunning movie that feels like a beautiful dream about memory",
    "sci-fi movies directed by Ridley Scott released in the 1980s",
    "an action movie directed by Quentin Tarantino with high ratings",
    "movies directed by Christopher Nolan with a runtime over 140 minutes",
    "a stop-motion animation movie about farm animals trying to escape",
    "a dry deadpan mockumentary about a computer chess tournament in the 80s",
    "a movie where a single actor is trapped in a confined space",
    "a heartwarming family movie with a strong message about friendship",
    "a gripping historical drama based on true events during World War 2",
    "a fast paced action movie with incredible car chases and practical stunts"
]

st.set_page_config(
    page_title="Algorithm Retrieval Analysis",
    layout="wide",
)

# -----------------------------------------------------------------------------
# LOGGING SETUP
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if "execution_logs" not in st.session_state:
    st.session_state["execution_logs"] = []

def emit_log(level: str, msg: str) -> None:
    """Registra eventos tanto en la salida estándar como en el estado de la UI."""
    log_line = f"[{level}] {msg}"
    st.session_state["execution_logs"].append(log_line)
    
    if level == "INFO":
        logging.info(msg)
    elif level in ["WARN", "WARNING"]:
        logging.warning(msg)
    elif level == "ERROR":
        logging.error(msg)
    else:
        logging.debug(msg)

# -----------------------------------------------------------------------------
# DATA ACCESS LAYER
# -----------------------------------------------------------------------------
def fetch_recommendations(query: str, model: str) -> List[Dict[str, Any]]:
    """Ejecuta la llamada a la API para obtener recomendaciones."""
    payload = {
        "query": query,
        "model": model,
        "max_results": 10,
        "max_runtime": 500,
    }
    emit_log("INFO", f"[{model}] Dispatching POST request to {API_URL}")
    
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        elapsed_time = round(time.time() - start_time, 2)
        emit_log("INFO", f"[{model}] HTTP {response.status_code} in {elapsed_time}s")
        
        data = response.json()
        return data.get("results", [])
        
    except requests.exceptions.RequestException as e:
        emit_log("ERROR", f"[{model}] Connection or processing error: {e}")
        return []

# -----------------------------------------------------------------------------
# PRESENTATION & EXECUTION LAYER
# -----------------------------------------------------------------------------
def main():
    st.title("Algorithm Retrieval Analysis")
    st.markdown(
        "Mide el volumen de documentos únicos recuperados por distintos algoritmos "
        "de recomendación para un conjunto predefinido de consultas."
    )

    log_expander = st.expander("Execution Logs", expanded=False)
    st.divider()

    if st.button("Ejecutar Análisis de Recuperación", type="primary", use_container_width=True):
        
        # Reset logs para cada ejecución
        st.session_state["execution_logs"] = [] 
        
        emit_log("INFO", f"Initializing test sequence. Models: {len(MODELS_TO_TEST)} | Queries: {len(TEST_QUERIES)}")

        retrieval_tracker: Dict[str, Set[str]] = {model: set() for model in MODELS_TO_TEST}
        progress_bar = st.progress(0)
        
        total_steps = len(TEST_QUERIES) * len(MODELS_TO_TEST)
        current_step = 0

        st.subheader("Recopilando resultados de la API...")

        for query in TEST_QUERIES:
            st.markdown(f"**Query:** `{query}`")
            columns = st.columns(len(MODELS_TO_TEST))

            for idx, model in enumerate(MODELS_TO_TEST):
                with columns[idx]:
                    with st.spinner(model):
                        movies = fetch_recommendations(query, model)
                        
                        if movies:
                            sample_titles = [m.get("title", "UNKNOWN_TITLE") for m in movies[:3]]
                            emit_log("INFO", f"[{model}] Top 3 matches: {sample_titles}")
                        else:
                            emit_log("WARN", f"[{model}] No documents retrieved.")

                        # Agregar títulos al set para contabilizar únicos
                        for movie in movies:
                            title = movie.get("title")
                            if title:
                                retrieval_tracker[model].add(title)

                        st.caption(f"Resultados: {len(movies)}")

                current_step += 1
                progress_bar.progress(current_step / total_steps)

        emit_log("INFO", "Data collection phase completed. Computing aggregates.")
        
        # --- Agregación de resultados ---
        results_data = []
        for model in MODELS_TO_TEST:
            unique_titles = retrieval_tracker[model]
            unique_count = len(unique_titles)
            
            results_data.append({
                "Algoritmo": model.capitalize(),
                "Títulos Únicos": unique_count
            })
            emit_log("INFO", f"Aggregated [{model}]: {unique_count} unique items.")

        # --- Visualización de métricas ---
        st.divider()
        st.subheader("Resultados de Recuperación")

        df_results = pd.DataFrame(results_data).set_index("Algoritmo")
        st.dataframe(df_results, use_container_width=True)

        df_plot = df_results.reset_index()

        chart = (
            alt.Chart(df_plot)
            .mark_bar()
            .encode(
                x=alt.X("Algoritmo:N", sort="-y", title=None),
                y=alt.Y("Títulos Únicos:Q", title="Volumen de Títulos Únicos"),
                color=alt.Color(
                    "Algoritmo:N",
                    scale=alt.Scale(scheme="blues"),
                    legend=None,
                ),
                tooltip=["Algoritmo", "Títulos Únicos"],
            )
            .properties(title="Volumen Total de Documentos Únicos por Algoritmo", height=400)
        )
        
        st.altair_chart(chart, use_container_width=True)
        emit_log("INFO", "Execution workflow finalized successfully.")

    # --- Renderizado del buffer de logs ---
    with log_expander:
        if st.session_state["execution_logs"]:
            st.code("\n".join(st.session_state["execution_logs"]), language="text")
        else:
            st.caption("Los logs de ejecución aparecerán aquí tras iniciar el proceso.")

if __name__ == "__main__":
    main()