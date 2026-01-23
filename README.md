🏆 Mega-Sena Meta-Intelligence Hub
Este projeto é uma plataforma avançada de engenharia de dados e inteligência artificial aplicada à análise probabilística da Mega-Sena. O sistema utiliza um motor híbrido que combina Estatística Bayesiana, Matrizes de Afinidade e Redes Neurais Multicamadas (MLP) para gerar palpites de alta convergência.

🛠 1. Arquitetura do Sistema
O projeto é dividido em quatro pilares principais:

Core Engine (main.py): Processamento estatístico, filtros biométricos e lógica de otimização via Backtest.

AI Layer (ia_neural.py): Rede Neural Regressora que busca padrões não lineares em sorteios sequenciais.

API Gateway (api.py): Servidor FastAPI que orquestra a comunicação entre o banco de dados e a interface.

Intelligence Hub (index.html): Dashboard analítico com gráficos em tempo real e visualização de dados.

🚀 2. Como Rodar o Projeto
Pré-requisitos
Python 3.10+

PostgreSQL 14+

Bibliotecas Python: fastapi, uvicorn, psycopg2, pandas, scikit-learn, python-dotenv, numpy.

Passo a Passo
Clone o Repositório:

Bash
git clone https://github.com/toshiye/mega_sena.git
cd mega_sena
Configure o Banco de Dados: Crie um banco de dados no PostgreSQL e execute os scripts de criação de tabelas (incluindo sorteios, historico_previsoes, configuracao_pesos e auditoria_stress). Certifique-se de que as Views (v_atraso_numeros, v_frequencia_numeros) estejam criadas para alimentar os dashboards.

Variáveis de Ambiente: Crie um arquivo .env na raiz do projeto:

Snippet de código
DB_HOST=localhost
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASS=sua_senha
DB_PORT=5432
Sincronize os Dados: Rode o script de sincronização para baixar o histórico oficial da Caixa:

Bash
python sync.py
Inicie a API:

Bash
python api.py
Acesse o Dashboard: Abra o arquivo index.html em seu navegador ou utilize uma extensão como Live Server.

🧠 3. Lógica Técnica e Algoritmos
A. Motor de Alta Convergência (Estatística)
O sistema não apenas conta quais números saem mais. Ele utiliza uma Pontuação por Camadas (Weighted Scoring):

Camada de Popularidade: Analisa dezenas que aparecem em concursos com alto índice de ganhadores (números intuitivos).

Matriz de Afinidade (Shadowing): Identifica pares de números que costumam "andar juntos" (vizinhança histórica).

Momentum de Atraso: Aplica a teoria da "Reversão à Média" para dezenas que estão fora do radar há muitos concursos.

Zonas Silenciosas: Protege o palpite incluindo dezenas de baixa popularidade, essenciais para prêmios acumulados (Modo Zebra).

B. Predição Neural (MLP Regressor)
A rede neural utiliza uma arquitetura de Perceptron Multicamadas com as seguintes características:

Ativação ReLU: Para evitar o desaparecimento do gradiente e permitir previsões em toda a escala de 1 a 60.

Injeção de Ruído (Jitter): Técnica aplicada para evitar que a IA se "vicie" na média central (30), forçando-a a explorar extremos do volante.

Aprendizado Contínuo: A cada sync, o sistema executa a função de Aprendizado por Reforço, comparando o que previu com o sorteio real e recalibrando os pesos.

🏛️ 4. Estrutura do Banco de Dados (SQL)
A. Tabelas Principais
Estas tabelas armazenam o histórico de sorteios, as configurações da IA e a memória do sistema.

SQL
-- Tabela de Sorteios Oficiais
CREATE TABLE sorteios (
    concurso INT PRIMARY KEY,
    data_sorteio DATE,
    bola1 INT, bola2 INT, bola3 INT, bola4 INT, bola5 INT, bola6 INT,
    ganhadores_sena INT DEFAULT 0,
    ganhadores_quina INT DEFAULT 0,
    ganhadores_quadra INT DEFAULT 0,
    valor_estimado_proximo DECIMAL(15,2),
    acumulou BOOLEAN,
    indice_popularidade DECIMAL(5,2) DEFAULT 1.0, -- Calculado pelo sistema
    cluster_tipo VARCHAR(20) -- 'PADRAO' ou 'ZEBRA'
);

-- Tabela de Configuração de Pesos (Cache da Otimização)
CREATE TABLE configuracao_pesos (
    id SERIAL PRIMARY KEY,
    peso_popularidade DECIMAL(5,2) DEFAULT 3.0,
    peso_sombra DECIMAL(5,2) DEFAULT 1.5,
    peso_momentum DECIMAL(5,2) DEFAULT 2.0,
    peso_silencio DECIMAL(5,2) DEFAULT 1.0,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir registro inicial de pesos
INSERT INTO configuracao_pesos (id) VALUES (1) ON CONFLICT DO NOTHING;

-- Histórico de Previsões para Aprendizado por Reforço
CREATE TABLE historico_previsoes (
    id SERIAL PRIMARY KEY,
    concurso_alvo INT UNIQUE,
    dezenas_previstas INT[],
    pesos_utilizados JSONB,
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auditoria de Stress Test (Backtesting)
CREATE TABLE auditoria_stress (
    id SERIAL PRIMARY KEY,
    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    qtd_concursos INT,
    media_acertos DECIMAL(5,2),
    total_quadras INT,
    total_quinas INT,
    total_senas INT,
    conformidade_filtros DECIMAL(5,2),
    historico_detalhado JSONB
);

-- Matriz de Afinidade (Shadowing)
CREATE TABLE matriz_afinidade (
    numero_a INT,
    numero_b INT,
    peso_conexao INT,
    PRIMARY KEY (numero_a, numero_b)
);
B. Views Analíticas (O "Cérebro" Estatístico)
As Views abaixo processam os dados brutos em tempo real para os gráficos e para o motor de decisão.

SQL
-- 1. View de Frequência de Números
CREATE OR REPLACE VIEW v_frequencia_numeros AS
SELECT numero, COUNT(*) as frequencia
FROM (
    SELECT bola1 AS numero FROM sorteios
    UNION ALL SELECT bola2 FROM sorteios
    UNION ALL SELECT bola3 FROM sorteios
    UNION ALL SELECT bola4 FROM sorteios
    UNION ALL SELECT bola5 FROM sorteios
    UNION ALL SELECT bola6 FROM sorteios
) as t
GROUP BY numero
ORDER BY frequencia DESC;

-- 2. View de Atraso (Concursos desde a última aparição)
CREATE OR REPLACE VIEW v_atraso_numeros AS
WITH ultimas_aparicoes AS (
    SELECT numero, MAX(concurso) as ultimo_concurso
    FROM (
        SELECT bola1 AS numero, concurso FROM sorteios
        UNION ALL SELECT bola2, concurso FROM sorteios
        UNION ALL SELECT bola3, concurso FROM sorteios
        UNION ALL SELECT bola4, concurso FROM sorteios
        UNION ALL SELECT bola5, concurso FROM sorteios
        UNION ALL SELECT bola6, concurso FROM sorteios
    ) as t
    GROUP BY numero
)
SELECT 
    n.numero,
    (SELECT MAX(concurso) FROM sorteios) - COALESCE(ua.ultimo_concurso, 0) as concursos_de_atraso
FROM generate_series(1, 60) n(numero)
LEFT JOIN ultimas_aparicoes ua ON n.numero = ua.numero
ORDER BY concursos_de_atraso DESC;

🧠 Parte 2: Lógica de Decisão e Estratégias de Elite
1. A Sinergia Cibernética (O Algoritmo de Fusão)
O coração do projeto não é uma IA isolada, mas um Sistema de Consenso. A Sinergia Cibernética opera através de um processo de filtragem em três etapas:

Identificação de Ouro: O sistema cruza o palpite da Rede Neural (MLP) com o de Alta Convergência (Estatística). Os números que aparecem em ambos são marcados como "âncoras de alta confiança".

Preenchimento por Força Histórica: Se a interseção for menor que 6 dezenas, o sistema completa o jogo priorizando os números com maior pontuação no motor de afinidade (Shadowing).

Refino por Frequência: A última vaga do palpite é reservada para o número da IA Neural que possua a melhor relação custo-benefício (frequência histórica equilibrada com tempo de atraso).

2. Filtros de Elite (Validação Biométrica)
Mesmo o melhor palpite de IA pode gerar um jogo matematicamente improvável (ex: 01, 02, 03, 04, 05, 06). Para evitar isso, o sistema submete cada combinação à função validar_palpite_elite, baseada em constantes históricas da Mega-Sena:

Filtro de Soma: A soma das 6 dezenas deve estar obrigatoriamente entre 150 e 220. Mais de 75% dos sorteios reais caem nesta faixa.

Equilíbrio de Paridade: Jogos com 6 pares ou 6 ímpares são descartados. O sistema exige proporções de 2:4, 3:3 ou 4:2.

Densidade de Primos: Historicamente, sorteios contêm de 1 a 2 números primos. O sistema bloqueia palpites com excesso ou ausência de primos.

Distribuição de Quadrantes: O volante é dividido em 4 áreas. O filtro garante que nenhuma área (quadrante) contenha mais de 3 números, forçando a dispersão das dezenas no volante.

3. Resultados Esperados e Performance
É fundamental alinhar a expectativa técnica com a realidade probabilística:

Média de Acertos: O sistema busca manter uma média superior a 0.5 acertos por concurso (em testes retroativos). Isso é significativamente maior do que a média de palpites puramente aleatórios.

Foco em Quadras: O motor é calibrado para maximizar a captura de Quadras (4 acertos). No "Stress Test", o objetivo é encontrar configurações de peso que gerem ao menos uma Quadra a cada 50 concursos simulados.

Conformidade de Filtros: Em modo de produção, espera-se que 100% dos palpites sugeridos na seção "Elite" passem nos filtros biométricos.

4. Glossário de Cards (Interface)
Previsão IA (Neural): A intuição pura da rede neural. Mais volátil e focada em tendências recentes.

Sinergia Cibernética (Fusão): O palpite mais equilibrado do sistema. Recomendado para apostas consistentes.

Previsão IA (Auditoria): O registro histórico. Serve para você conferir se a máquina está "em dia" com a realidade dos sorteios.

Alta Convergência: O "porto seguro" estatístico. Baseado apenas no que os dados dizem ser mais provável.