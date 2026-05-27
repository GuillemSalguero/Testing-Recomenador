## 9.6. Avaluació Analítica de l'Arquitectura RAG

El rendiment del sistema de recuperació s'ha avaluat mitjançant una bateria de proves dissenyades per mesurar tres dimensions crítiques del pipeline: **rellevància de les respostes**, **recall (cobertura) del catàleg** i **dispersió geomètrica (diversitat) dels resultats**. 

Per garantir una avaluació determinista i sense biaixos, els cinc mòduls de retrieval s'han sotmès a les mateixes 12 queries d'estrès, dissenyades per forçar diferents vectors de cerca (metadades explícites, semàntica abstracta, nínxol i lògica contradictòria).

### 9.6.1. Avaluació Heurística (LLM-as-a-Judge)
Aquest mòdul utilitza `Llama-3.3-70B` com a avaluador automatitzat per quantificar la precisió contextual de les recomanacions.

* **Metodologia:** L'avaluador processa els top-K documents (K=10) recuperats per cada mòdul —incloent títol, any, metadades de gènere i mètriques de validació (Tomatometer)— i computa una puntuació (1-100) basada en la satisfacció global de la intenció de cerca.
* **Criteris de penalització:** Es penalitza severament (≤ 25) la pèrdua de filtres durs o la inclusió de soroll en l'espai vectorial, mentre que s'atorga la màxima puntuació (100) a una llista de resultats amb alta precisió semàntica i lògica.
* **Anàlisi de resultats:** * Els algorismes de **Self-Querying** i **Hybrid Search** maximitzen el rendiment en consultes amb metadades explícites. Això s'aconsegueix mitjançant l'extracció de paràmetres i l'aplicació de filtres estructurats pre-similitud, reduint l'espai de cerca vectorial i mitigant el risc de falsos positius semàntics.
  * Els mòduls **Combined** i **Multi-Query** mostren un rendiment superior en queries abstractes. L'expansió del latent space mitjançant reformulació de consultes permet capturar connexions emocionals o atmosfèriques sense dependre d'un mapatge lèxic exacte.


### 9.6.2. Exploració i Cobertura del Corpus (Algorithm Retrieval)
Aquesta mètrica quantifica el volum de documents únics activats per cada mòdul, avaluant l'eficiència de l'algorisme en l'exploració de l'espai de dades disponible (mesura proxy del recall del sistema).

* **Metodologia:** Execució en batch de les 12 queries sobre els 5 mòduls, agregant els resultats en un set no duplicat. El límit teòric de cobertura se situa en 120 documents per mòdul (assumint una intersecció nul·la).
* **Anàlisi de resultats:**
  * El mòdul de **Parent Retrieval** lidera aquesta mètrica. La seva arquitectura d'indexació per reconstrucció de context (agregació de chunks fill cap a un document pare) amplia la superfície d'activació vectorial, evitant la pèrdua de context pròpia de la partició de dades tradicional.
  * El mòdul **Hybrid** també manté una taxa de descobriment alta gràcies a la fusió de l'scoring dens (embeddings) i l'espars (BM25), minimitzant els punts cecs estructurals de cada mètode aïllat.


### 9.6.3. Variància Intra-Llista (Intra-List Diversity - ILD)
L'ILD mesura la dispersió dels documents recuperats dins d'un mateix set de resultats, quantificant la capacitat del sistema per evitar el col·lapse de diversitat.

* **Funció de distància:** Es calcula la distància geomètrica mitjana entre tots els parells del top-K mitjançant una funció de costos ponderada:
  * **Gènere (50%) i Director (30%):** Avaluats mitjançant distància de Jaccard sobre els conjunts d'etiquetes.
  * **Any d'estrena (20%):** Avaluat mitjançant distància temporal normalitzada sobre una finestra estàndard de 40 anys.
* **Anàlisi de resultats:** La mètrica oscil·la entre 0 (homogeneïtat total) i 1 (màxima dispersió). Els mòduls **Combined** i **Multi-Query** demostren la variància d'ILD més eficient: forcen la convergència (ILD baix) en presència de filtres durs definits per l'usuari, i maximitzen l'exploració (ILD alt) en sol·licituds no restringides.


---

## Desplegament de l'Entorn d'Avaluació

Per inicialitzar el dashboard analític desenvolupat amb Streamlit, assegureu-vos de tenir l'entorn virtual activat i executeu la següent instrucció a la línia de comandes:

```bash
streamlit run app.py
