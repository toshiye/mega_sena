# 🎰 Mega-Sena Meta-Intelligence Hub

An advanced **Data Engineering** and **Artificial Intelligence** platform applied to probabilistic analysis. This system employs a hybrid engine combining **Bayesian Statistics**, **Affinity Matrices**, and **Multi-Layer Perceptron (MLP) Neural Networks** to generate high-convergence predictions.

---

## 🛠 1. System Architecture
The project is structured into four high-performance pillars:

1. **Core Engine (`main.py`):** Statistical processing, **biometric filtering**, and **Backtest-driven** optimization logic.
2. **AI Layer (`ia_neural.py`):** A **Neural Regressor** designed to identify non-linear patterns in sequential draws.
3. **API Gateway (`api.py`):** A robust **FastAPI** server orchestrating communication between the database and the interface.
4. **Intelligence Hub (`index.html`):** An analytical dashboard featuring **real-time charts** and complex data visualization.

---

## 🧠 2. AI Logic & Elite Strategy: "Cybernetic Synergy"
The system utilizes a **Fusion Algorithm** that intersects Neural Networks with Bayesian Statistics:

* **Anchors:** Numbers identified by both models receive maximum weighting.
* **Refinement:** The AI operates on the "margin of error," suggesting numbers that break purely linear trends.

### **Biometric Filters (Elite Validation)**
No prediction is displayed without passing strict feasibility constraints:
* **Sum Range:** Optimized between 150 and 220.
* **Parity:** Balanced ratio of Even/Odd (2:4, 3:3, 4:2).
* **Prime Numbers:** Controlled presence (1 to 2 primes per game).
* **Quadrants:** Spatial distribution across the ticket to avoid clusters.

---

## 🏛️ 3. Database Schema & SQL Engineering
The persistence layer is designed for high-performance analytical queries using **PostgreSQL 14+**.

### **Key Tables & Advanced Views**
```sql
-- Main Draws Table with Clustering and Popularity Index
CREATE TABLE sorteios (
    concurso INT PRIMARY KEY,
    data_sorteio DATE,
    bola1 INT, bola2 INT, bola3 INT, bola4 INT, bola5 INT, bola6 INT,
    ganhadores_sena INT DEFAULT 0,
    valor_estimado_proximo DECIMAL(15,2),
    acumulou BOOLEAN,
    indice_popularidade DECIMAL(5,2) DEFAULT 1.0,
    cluster_tipo VARCHAR(20)
);

-- Advanced View for Number Frequency Analysis
CREATE OR REPLACE VIEW v_frequencia_numeros AS
SELECT numero, COUNT(*) as frequencia
FROM (
    SELECT bola1 AS numero FROM sorteios UNION ALL SELECT bola2 FROM sorteios
    UNION ALL SELECT bola3 FROM sorteios UNION ALL SELECT bola4 FROM sorteios
    UNION ALL SELECT bola5 FROM sorteios UNION ALL SELECT bola6 FROM sorteios
) as t GROUP BY numero ORDER BY frequencia DESC;

-- CTE-based View for Recency/Delay Analysis (Gap Analysis)
CREATE OR REPLACE VIEW v_atraso_numeros AS
WITH ultimas_aparicoes AS (
    SELECT numero, MAX(concurso) as ultimo_concurso
    FROM (
        SELECT bola1 AS numero, concurso FROM sorteios UNION ALL SELECT bola2, concurso FROM sorteios
        UNION ALL SELECT bola3, concurso FROM sorteios UNION ALL SELECT bola4, concurso FROM sorteios
        UNION ALL SELECT bola5, concurso FROM sorteios UNION ALL SELECT bola6, concurso FROM sorteios
    ) as t GROUP BY numero
)
SELECT n.numero, (SELECT MAX(concurso) FROM sorteios) - COALESCE(ua.ultimo_concurso, 0) as concursos_de_atraso
FROM generate_series(1, 60) n(numero)
LEFT JOIN ultimas_aparicoes ua ON n.numero = ua.numero;
```
## 🚀 4. How to Run
Prerequisites
Python 3.10+ | PostgreSQL 14+

Key Libs: fastapi, scikit-learn, pandas, psycopg2, numpy.

Installation
1. Clone & Setup:

``` Bash
git clone https://github.com/toshiye/mega_sena.git
cd mega_sena
pip install -r requirements.txt
```
2. Environment Variables (.env): Configure your DB_HOST, DB_NAME, DB_USER, and DB_PASS.

3. Sync & Execute:

```Bash
python sync.py  # Download official historical data
python api.py   # Start server at http://localhost:8000
📈 5. Expected Results & Backtesting
The engine is fine-tuned for "Quadra Maximization". Through rigorous Stress Testing (Backtesting), the system is recalibrated to identify probability zones where hit density consistently outperforms random selection in long-term simulations.
```
