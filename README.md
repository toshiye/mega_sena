# 🏆 Mega-Sena Meta-Intelligence Hub

Este projeto é uma plataforma avançada de engenharia de dados e inteligência artificial aplicada à análise probabilística da Mega-Sena. O sistema utiliza um motor híbrido que combina **Estatística Bayesiana**, **Matrizes de Afinidade** e **Redes Neurais Multicamadas (MLP)** para gerar palpites de alta convergência.

---

## 🛠 1. Arquitetura do Sistema

O projeto é estruturado em quatro pilares principais:
1.  **Core Engine (`main.py`):** Processamento estatístico, filtros biométricos e lógica de otimização via Backtest.
2.  **AI Layer (`ia_neural.py`):** Rede Neural Regressora que busca padrões não lineares em sorteios sequenciais.
3.  **API Gateway (`api.py`):** Servidor FastAPI que orquestra a comunicação entre o banco de dados e a interface.
4.  **Intelligence Hub (`index.html`):** Dashboard analítico com gráficos em tempo real e visualização de dados.

---

## 🚀 2. Como Rodar o Projeto

### Pré-requisitos
* **Python 3.10+**
* **PostgreSQL 14+**
* **Bibliotecas:** `fastapi`, `uvicorn`, `psycopg2`, `pandas`, `scikit-learn`, `python-dotenv`, `numpy`.

### Instalação e Execução

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/toshiye/mega_sena.git](https://github.com/toshiye/mega_sena.git)
    cd mega_sena
    ```

2.  **Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto:
    ```env
    DB_HOST=localhost
    DB_NAME=seu_banco
    DB_USER=seu_usuario
    DB_PASS=sua_senha
    DB_PORT=5432
    ```

3.  **Sincronize e Inicie:**
    ```bash
    python sync.py  # Baixa histórico oficial
    python api.py   # Inicia o servidor em http://localhost:8000
    ```

---

## 🏛️ 3. Estrutura do Banco de Dados (SQL)

Execute os comandos abaixo no seu PostgreSQL para garantir a compatibilidade total com o sistema.

### Tabelas Principais
```sql
CREATE TABLE sorteios (
    concurso INT PRIMARY KEY,
    data_sorteio DATE,
    bola1 INT, bola2 INT, bola3 INT, bola4 INT, bola5 INT, bola6 INT,
    ganhadores_sena INT DEFAULT 0,
    ganhadores_quina INT DEFAULT 0,
    ganhadores_quadra INT DEFAULT 0,
    valor_estimado_proximo DECIMAL(15,2),
    acumulou BOOLEAN,
    indice_popularidade DECIMAL(5,2) DEFAULT 1.0,
    cluster_tipo VARCHAR(20)
);

CREATE TABLE historico_previsoes (
    id SERIAL PRIMARY KEY,
    concurso_alvo INT UNIQUE,
    dezenas_previstas INT[],
    pesos_utilizados JSONB,
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE VIEW v_frequencia_numeros AS
SELECT numero, COUNT(*) as frequencia
FROM (
    SELECT bola1 AS numero FROM sorteios UNION ALL SELECT bola2 FROM sorteios
    UNION ALL SELECT bola3 FROM sorteios UNION ALL SELECT bola4 FROM sorteios
    UNION ALL SELECT bola5 FROM sorteios UNION ALL SELECT bola6 FROM sorteios
) as t GROUP BY numero ORDER BY frequencia DESC;

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

## 🧠 4. Lógica de IA e Estratégia de Elite
Sinergia Cibernética (Fusão)
O sistema utiliza um algoritmo de fusão que cruza a Rede Neural com a Estatística Bayesiana.

Âncoras: Números presentes em ambos os modelos ganham peso máximo.

Refino: A IA atua na "margem de erro", sugerindo dezenas que quebram tendências puramente lineares.

Filtros Biométricos (Validação de Elite)
Nenhum palpite é exibido sem passar por filtros de viabilidade:

Soma: Entre 150 e 220.

Paridade: Equilíbrio entre Pares e Ímpares (2:4, 3:3, 4:2).

Primos: Presença controlada de 1 a 2 números primos por jogo.

Quadrantes: Distribuição espacial no volante para evitar aglomerações.

## 📊 5. Glossário do Dashboard
Card,Origem,Função
Previsão IA (Neural),IA Viva,"Detecta tendências caóticas e ""Zebras""."
Sinergia Cibernética,Híbrido,O consenso de maior confiança do sistema.
Previsão IA (Auditoria),Banco de Dados,O palpite oficial registrado no último sync.
Alta Convergência,Estatística,Baseado puramente na frequência e atraso histórico.

## 📈 6. Resultados Esperados
O sistema é projetado para Maximização de Quadras. Através do "Stress Test" (Backtesting), o motor é recalibrado para encontrar zonas de probabilidade onde a densidade de acertos é superior à escolha aleatória, visando retornos consistentes em simulações de longo prazo.