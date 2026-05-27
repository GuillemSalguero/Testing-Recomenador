import os
import time
import requests
import pandas as pd
import altair as alt
import streamlit as st
import GROQ_KEY as groq_key
import re

from langchain_groq import ChatGroq

st.set_page_config(page_title="Evaluación RAG TFG", page_icon="🎬", layout="wide")

st.title("🎬 Evaluación Analítica de Algoritmos RAG (Por Categorías)")
st.markdown("Este panel evalúa 5 algoritmos enfrentándolos a diferentes tipos de estrés exigiendo el Top 10 de resultados y evaluando sobre 100 puntos.")





os.environ["GROQ_API_KEY"] = groq_key.obtener_api_key()

API_URL = "http://localhost:8001/api/recommend"
MODELS_TO_TEST = ["self_query", "hybrid", "multi_query", "combined", "parent"]

test_cases = [
    {"cat": "1. Abstracta", "prompt": "a profound psychological thriller that leaves you questioning reality and human existence"},
    {"cat": "1. Abstracta", "prompt": "a movie that perfectly captures the feeling of profound loneliness in a modern big city"},
    {"cat": "1. Abstracta", "prompt": "a visually stunning movie that feels like a beautiful dream and deals with memory"},
    {"cat": "2. Directores/Metadatos", "prompt": "cosy movies directed by Bill Melendez"},
    {"cat": "2. Directores/Metadatos", "prompt": "an action movie directed by Masaki Kobayashi of the 1970s"},
    {"cat": "2. Directores/Metadatos", "prompt": "movies directed by Christopher Nolan with a runtime over 140 minutes"},
    {"cat": "3. Raras / Nicho", "prompt": "a stop-motion animation movie about farm animals trying to escape or having an adventure"},
    {"cat": "3. Raras / Nicho", "prompt": "a dry deadpan mockumentary about a computer chess tournament in the 80s"},
    {"cat": "3. Raras / Nicho", "prompt": "a movie where a single actor is trapped in a confined space for almost the entire runtime"},
    {"cat": "4. Contradictoria", "prompt": "a terrifying and gory romantic comedy for toddlers and kids under 5 years old"},
    {"cat": "4. Contradictoria", "prompt": "a silent movie from the 1920s directed by Steven Spielberg about the internet"},
    {"cat": "4. Contradictoria", "prompt": "a fast paced action movie with absolutely no fights, no explosions, and everyone just sits in silence"}
]

@st.cache_resource
def get_llm_judge():
    return ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)

llm_judge = get_llm_judge()

def evaluate_relevance(prompt: str, movies: list) -> tuple:
    if not movies:
        return 1, "No se recibieron resultados."
    
    movie_info = "\n".join([
        f"- {m.get('title', 'Sin título')} ({m.get('year', 'N/A')}): {m.get('genres', 'N/A')} | Tomatometer: {m.get('signals', {}).get('tomatometer', 'N/A')}" 
        for m in movies
    ])
    
    eval_prompt = f"""
    Eres un crítico de cine muy estricto. El usuario pidió: "{prompt}".
    El sistema recomendó esta lista de {len(movies)} películas:\n{movie_info}\n
    
    Puntúa del 1 al 100 qué tan bien cumple LA LISTA EN SU CONJUNTO con la petición.
    - 100: Las 10 películas son perfectas y cumplen todo.
    - 75: Las primeras son buenas, pero hay algo de relleno irrelevante.
    - 50: Mitad aciertos, mitad errores garrafales.
    - 25 o menos: Casi toda la lista es basura irrelevante o ignora filtros duros.
    
    Si la petición es contradictoria o tramposa, puntúa alto (80-100) si el sistema resolvió el problema de forma inteligente.
    
    Responde EXACTAMENTE en este formato:
    PUNTUACION: [número del 1 al 100]
    RAZONAMIENTO: [2-3 frases explicando por qué]
    """
    try:
        response = llm_judge.invoke(eval_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        score_match = re.search(r'PUNTUACION:\s*(\d+)', response_text)
        reason_match = re.search(r'RAZONAMIENTO:\s*(.+)', response_text, re.DOTALL)
        
        score = max(1, min(int(score_match.group(1)), 100)) if score_match else 1
        reason = reason_match.group(1).strip() if reason_match else "Sin razonamiento."
        
        return score, reason
    except Exception as e:
        return 1, f"Error: {e}"

st.info(f"Se evaluarán {len(test_cases)} prompts categorizados en {len(MODELS_TO_TEST)} modelos exigiendo 10 resultados.")

if st.button("Iniciar Análisis de Profundidad Masivo", type="primary"):
    
    progress_bar = st.progress(0)
    results_data = []
    total_steps = len(test_cases) * len(MODELS_TO_TEST)
    current_step = 0

    for case in test_cases:
        cat = case["cat"]
        prompt = case["prompt"]
        st.markdown(f"---\n**[{cat}]** `{prompt}`")
        cols = st.columns(len(MODELS_TO_TEST))
        
        for idx, model in enumerate(MODELS_TO_TEST):
            with cols[idx]:
                st.markdown(f"**{model}**")
                with st.spinner(f"Consultando..."):
                    payload = {"query": prompt, "model": model, "max_results": 5, "max_runtime": 500}
                    start_time = time.time()
                    
                    try:
                        response = requests.post(API_URL, json=payload)
                        response.raise_for_status()
                        movies = response.json().get("results", [])
                        latency = time.time() - start_time
                        
                        score, reason = evaluate_relevance(prompt, movies)
                        
                        results_data.append({
                            "Categoría": cat,
                            "Prompt": prompt[:30] + "...",
                            "Algoritmo": model.capitalize(),
                            "Latencia (s)": round(latency, 2),
                            "Relevancia (1-100)": score
                        })

                        st.success(f"{score}/100  ({latency:.1f}s)")
                        
                        with st.expander("🎬 Películas"):
                            for m in movies:
                                title = m.get('title', m.get('link', '?'))
                                year = m.get('year', '?')
                                genres = m.get('genres', '?')
                                tom = m.get('signals', {}).get('tomatometer', '?')
                                st.markdown(f"**{title}** ({year}) — {genres} |  {tom}")
                        
                        with st.expander(" Razonamiento del juez"):
                            st.markdown(reason)
                                    
                    except Exception as e:
                        latency = time.time() - start_time
                        st.error(f"Error ❌")
                        results_data.append({
                            "Categoría": cat,
                            "Prompt": prompt[:30] + "...",
                            "Algoritmo": model.capitalize(),
                            "Latencia (s)": round(latency, 2),
                            "Relevancia (1-100)": 1
                        })
            
            current_step += 1
            progress_bar.progress(current_step / total_steps)

    st.markdown("---")
    st.header(" Resultados Finales")
    
    if results_data:
        df = pd.DataFrame(results_data)
        
        # Tabla resumen
        st.subheader("Puntuación media por algoritmo")
        summary = df.groupby("Algoritmo")["Relevancia (1-100)"].mean().reset_index()
        summary.columns = ["Algoritmo", "Puntuación Media"]
        summary = summary.sort_values("Puntuación Media", ascending=False)
        st.dataframe(summary, use_container_width=True)

        # Gráfico por categoría
        st.subheader("Puntuación por categoría y algoritmo")
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Algoritmo:N"),
            y=alt.Y("mean(Relevancia (1-100)):Q", title="Puntuación Media"),
            color="Algoritmo:N",
            column="Categoría:N"
        ).properties(width=150)
        st.altair_chart(chart)

        # Latencia media
        st.subheader("Latencia media por algoritmo")
        lat_summary = df.groupby("Algoritmo")["Latencia (s)"].mean().reset_index()
        lat_summary.columns = ["Algoritmo", "Latencia Media (s)"]
        lat_summary = lat_summary.sort_values("Latencia Media (s)")
        st.dataframe(lat_summary, use_container_width=True)

        # Tabla completa
        st.subheader("Resultados completos")
        st.dataframe(df, use_container_width=True)