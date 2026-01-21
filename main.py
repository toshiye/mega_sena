import psycopg2
import os
import random
import itertools
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTES GLOBAIS ---
# Dezenas que historicamente acumulam mais por serem menos jogadas
ZONAS_SILENCIOSAS = [41, 42, 43, 51, 52, 53, 54, 58, 59, 60]
# Dezenas com maior frequência histórica (corrigido erro de zeros à esquerda)
DEZENAS_MAIS_FREQUENTES_HISTORICAS = [10, 53, 5, 37, 23, 33, 4, 41, 30, 42]

def conectar_banco():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

# --- FUNÇÕES DE APOIO ESTATÍSTICO ---

def obter_analise_sql():
    conn = conectar_banco()
    cur = conn.cursor()
    
    # 1. Histórico Total
    cur.execute("SELECT numero, COUNT(*) FROM v_frequencia_numeros GROUP BY numero ORDER BY COUNT DESC;")
    hist = cur.fetchall()

    # 2. Janela Recente (20 concursos)
    query_recente = """
        WITH ultimos_sorteios AS (
            SELECT bola1, bola2, bola3, bola4, bola5, bola6 
            FROM sorteios ORDER BY concurso DESC LIMIT 20
        )
        SELECT numero, COUNT(*) FROM (
            SELECT bola1 AS numero FROM ultimos_sorteios
            UNION ALL SELECT bola2 FROM ultimos_sorteios
            UNION ALL SELECT bola3 FROM ultimos_sorteios
            UNION ALL SELECT bola4 FROM ultimos_sorteios
            UNION ALL SELECT bola5 FROM ultimos_sorteios
            UNION ALL SELECT bola6 FROM ultimos_sorteios
        ) t GROUP BY numero ORDER BY COUNT DESC;
    """
    cur.execute(query_recente)
    rec = cur.fetchall()

    # 3. Atraso (Maduros)
    cur.execute("SELECT numero FROM v_atraso_numeros ORDER BY concursos_de_atraso DESC;")
    atraso = cur.fetchall()

    cur.close()
    conn.close()
    return hist, rec, atraso

def gerar_jogo(lista_base, quantidade=15):
    """Extrai uma lista de inteiros de tuplas SQL."""
    return [int(n[0]) for n in lista_base[:quantidade]]

def obter_dezenas_por_popularidade(limite_popularidade=1.2, top=20):
    conn = conectar_banco()
    cur = conn.cursor()
    query = """
        WITH sorteios_populares AS (
            SELECT bola1, bola2, bola3, bola4, bola5, bola6 
            FROM sorteios WHERE indice_popularidade >= %s
        ),
        contagem AS (
            SELECT numero, COUNT(*) as freq FROM (
                SELECT bola1 AS numero FROM sorteios_populares UNION ALL SELECT bola2 FROM sorteios_populares
                UNION ALL SELECT bola3 FROM sorteios_populares UNION ALL SELECT bola4 FROM sorteios_populares
                UNION ALL SELECT bola5 FROM sorteios_populares UNION ALL SELECT bola6 FROM sorteios_populares
            ) t GROUP BY numero
        )
        SELECT numero FROM contagem ORDER BY freq DESC LIMIT %s;
    """
    cur.execute(query, (limite_popularidade, top))
    res = cur.fetchall()
    cur.close()
    conn.close()
    return [int(n[0]) for n in res]

def obter_matriz_vizinhanca_historica(top=10):
    conn = conectar_banco()
    cur = conn.cursor()
    # Adicionamos um filtro WHERE para garantir que não pegamos nulos durante o reprocessamento
    cur.execute("""
        SELECT numero_b, SUM(peso_conexao) as forca 
        FROM matriz_afinidade 
        WHERE numero_b IS NOT NULL 
        GROUP BY numero_b 
        ORDER BY forca DESC LIMIT %s
    """, (top,))
    res = cur.fetchall()
    cur.close()
    conn.close()
    return [int(n[0]) for n in res if n[0] is not None]

def obter_dezenas_momentum(min_atraso=3, max_atraso=15, top=10):
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute("SELECT numero FROM v_atraso_numeros WHERE concursos_de_atraso BETWEEN %s AND %s ORDER BY concursos_de_atraso ASC LIMIT %s", (min_atraso, max_atraso, top))
    res = cur.fetchall()
    cur.close()
    conn.close()
    return [int(n[0]) for n in res]

# --- MOTOR DE OTIMIZAÇÃO (BACKTEST) ---

def otimizar_pesos_convergencia(limite_backtest=10):
    """
    Analisa os últimos concursos para definir os melhores pesos das camadas,
    focando em maximizar acertos de Quadra, Quina e Sena.
    Salva o resultado na tabela configuracao_pesos.
    """
    conn = conectar_banco()
    cur = conn.cursor()
    
    # Busca os resultados reais mais recentes para o teste
    cur.execute("""
        SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6 
        FROM sorteios ORDER BY concurso DESC LIMIT %s
    """, (limite_backtest,))
    resultados_reais = cur.fetchall()
    cur.close()
    conn.close()

    # Definição das faixas de peso para testar (Grid Search)
    faixas = [1.0, 2.0, 3.0]
    melhor_config = {"pop": 3.0, "som": 1.5, "sil": 1.0, "mom": 2.0}
    melhor_pontuacao = -1

    # Pré-carregamento dos dados das camadas (ganho de performance)
    populares = obter_dezenas_por_popularidade(top=15)
    sombras = obter_matriz_vizinhanca_historica(top=10)
    momentum = obter_dezenas_momentum()
    
    # Obtemos o histórico para definir o "ruído" dinamicamente
    hist_base, _, _ = obter_analise_sql()
    dezenas_ruido = [int(n[0]) for n in hist_base[:10]]

    print(f"Iniciando Otimização (Backtest) nos últimos {limite_backtest} concursos...")

    # Loop de combinações de pesos
    for p_pop in faixas:
        for p_som in faixas:
            for p_mom in faixas:
                acertos_totais = 0
                
                for res in resultados_reais:
                    gabarito = set(res[1:])
                    
                    # Simula o motor de pontuação para esta combinação específica
                    teste_pesos = Counter()
                    for n in populares: teste_pesos[n] += p_pop
                    for n in sombras: teste_pesos[n] += p_som
                    for n in ZONAS_SILENCIOSAS: teste_pesos[n] += 1.0
                    for n in dezenas_ruido: teste_pesos[n] += 1.0
                    for n in momentum: teste_pesos[n] += p_mom
                    
                    # Gera o palpite de 6 números desta simulação
                    palpite = [n for n, c in teste_pesos.most_common(6)]
                    acertos = len(set(palpite).intersection(gabarito))
                    
                    # --- NOVA LÓGICA DE PONTUAÇÃO (FOCO EM GRANDES PRÊMIOS) ---
                    # NOVA TABELA DE RECOMPENSA (REINFORCEMENT LEARNING)
                    if acertos == 6: 
                        pontos_tentativa = 5000  # Foco na Sena
                    elif acertos == 5: 
                        pontos_tentativa = 800   # Quina agora vale 80x mais que o normal
                    elif acertos == 4: 
                        pontos_tentativa = 50    # Quadra vale 5x mais que o terno
                    elif acertos == 3:
                        pontos_tentativa = 5     # Terno é apenas um "bom sinal"
                    else:
                        pontos_tentativa = 0     # 0, 1 ou 2 acertos são considerados erro total
                        
                    acertos_totais += pontos_tentativa

                # Verifica se esta combinação de pesos superou a anterior
                if acertos_totais > melhor_pontuacao:
                    melhor_pontuacao = acertos_totais
                    melhor_config = {
                        "pop": p_pop, 
                        "som": p_som, 
                        "sil": 1.0, 
                        "mom": p_mom
                    }

    # Salva a melhor configuração encontrada no banco de dados (Cache)
    salvar_pesos_otimizados(melhor_config)
    
    print(f"Otimização concluída! Melhor Pontuação Histórica: {melhor_pontuacao}")
    print(f"Pesos salvos: {melhor_config}")
    
    return melhor_config

# --- PROCESSAMENTO PRINCIPAL ---

def processar_todas_estrategias():
    """
    Motor Central de Decisão: Orquestra todas as camadas estatísticas,
    aplica pesos adaptativos via Clusters e integra a lógica de Ciclos.
    """
    conn = conectar_banco()
    cur = conn.cursor()
    
    # 1. Identificação da Tendência via Clusters (Padrão vs Zebra)
    cur.execute("SELECT cluster_tipo FROM sorteios ORDER BY concurso DESC LIMIT 3")
    ultimos_clusters = [r[0] for r in cur.fetchall()]
    # Lógica de Reversão à Média: Se muito caos, espera-se ordem (e vice-versa)
    tendencia_proxima = "PADRAO" if ultimos_clusters.count("ZEBRA") >= 2 else "ZEBRA"

    # 2. Obtenção dos Dados Base
    hist, rec, atraso = obter_analise_sql()
    
    # 3. Definição de Pesos Base (IA Cache)
    try:
        config = obter_pesos_cache()
    except:
        config = {"pop": 3.0, "som": 1.5, "mom": 2.0, "sil": 1.0}

    # AJUSTE DINÂMICO POR CLUSTER
    if tendencia_proxima == "PADRAO":
        config["pop"] *= 1.5  # Fortalece números quentes
        config["som"] *= 1.2  # Fortalece vizinhança comum
    else:
        config["sil"] *= 2.0  # Explora zonas esquecidas
        config["mom"] *= 1.5  # Busca números muito atrasados

    # --- CAMADA 1: LÓGICAS ESPECIALISTAS (BASE) ---
    e1_mais_saem  = gerar_jogo(hist, 15)
    e2_menos_saem = [int(n[0]) for n in hist[-15:]]
    e3_recente    = gerar_jogo(rec, 15)
    e4_atrasados  = gerar_jogo(atraso, 15)
    e6_aleatoria  = random.sample([int(n[0]) for n in hist], 6)

    # --- CAMADA 2: META-LÓGICA (CONSENSO) ---
    pool_de_numeros = e1_mais_saem + e3_recente + e4_atrasados + e6_aleatoria
    contagem_pool = Counter(pool_de_numeros)
    meta_frequentes = [n for n, c in contagem_pool.most_common(6)]

    # --- CAMADA 3: MOTOR DE ALTA CONVERGÊNCIA (PONTUAÇÃO FINAL) ---
    pesos_final = Counter()
    
    # Sub-camada A: Popularidade
    populares = obter_dezenas_por_popularidade(top=15)
    for n in populares: pesos_final[n] += config["pop"]

    # Sub-camada B: Sombras/Vizinhança
    sombras = obter_matriz_vizinhanca_historica(top=10)
    for n in sombras: pesos_final[n] += config["som"]

    # Sub-camada C: Ruído e Zonas Silenciosas
    for n in ZONAS_SILENCIOSAS: pesos_final[n] += config["sil"]
    dezenas_ruido = [int(n[0]) for n in hist[:10]]
    for n in dezenas_ruido: pesos_final[n] += 1.0

    # Sub-camada D: Momentum (Atraso)
    momentum = obter_dezenas_momentum()
    for n in momentum: pesos_final[n] += config["mom"]
    
    # Sub-camada E: Ciclo de Fechamento (Urgência)
    dezenas_pendentes = obter_dezenas_pendentes_ciclo()
    pesos_urgencia = calcular_peso_urgencia(dezenas_pendentes)
    for n, peso_extra in pesos_urgencia.items():
        pesos_final[n] += peso_extra

    # Bônus de Reforço (Convergência)
    for n in meta_frequentes: pesos_final[n] += 2.0

    # 4. GERAÇÃO DOS CONJUNTOS FINAIS (PERFIS)
    # Conjunto 1: Alta Convergência (Otimizado pela IA)
    palpite_ia = gerar_alta_convergencia_filtrada(pesos_final)

    cur.close()
    conn.close()

    return {
        "base": {
            "Mais Saem": sorted(e1_mais_saem[:6]),
            "Tendência Recente": sorted(e3_recente[:6]),
            "Números Atrasados": sorted(e4_atrasados[:6]),
            "Aleatório": sorted(e6_aleatoria)
        },
        "meta": {
            "Alta Convergência": sorted(palpite_ia),
            "Favoritos do Grupo": sorted(meta_frequentes),
            "Misto do Grupo": sorted(random.sample(list(set(palpite_ia + meta_frequentes)), 6)) # Adicionado para o HTML não quebrar
        },
        "debug_ia": {
            "tendencia_detectada": tendencia_proxima,
            "total_pendentes": len(dezenas_pendentes)
        }
    }

def processar_matriz_afinidade():
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute("DELETE FROM matriz_afinidade;")
    cur.execute("SELECT bola1, bola2, bola3, bola4, bola5, bola6 FROM sorteios WHERE indice_popularidade > 1.0")
    sorteios = cur.fetchall()
    
    conexoes = Counter()
    for s in sorteios:
        nums = sorted(list(s))
        for par in itertools.combinations(nums, 2):
            conexoes[par] += 1
            
    for (a, b), peso in conexoes.items():
        cur.execute("INSERT INTO matriz_afinidade (numero_a, numero_b, peso_conexao) VALUES (%s, %s, %s)", (a, b, peso))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Matriz de Afinidade atualizada!")

# Funções extras (simular_performance e analisar_ancoras_sorteio) permanecem iguais
    
def simular_performance(dezenas_palpite, limite_concursos=50):
    conn = conectar_banco()
    cur = conn.cursor()
    
    # Busca os últimos X resultados reais
    cur.execute("""
        SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6 
        FROM sorteios ORDER BY concurso DESC LIMIT %s
    """, (limite_concursos,))
    sorteios_reais = cur.fetchall()
    cur.close()
    conn.close()

    historico_acertos = []
    palpite_set = set(dezenas_palpite)

    for s in reversed(sorteios_reais): # Do mais antigo para o mais novo
        concurso = s[0]
        dezenas_reais = set(s[1:])
        acertos = len(palpite_set.intersection(dezenas_reais))
        historico_acertos.append({"concurso": concurso, "acertos": acertos})
        
    return historico_acertos

def analisar_ancoras_sorteio(concurso_id):
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute("SELECT bola1, bola2, bola3, bola4, bola5, bola6 FROM sorteios WHERE concurso = %s", (concurso_id,))
    sorteio = cur.fetchone()
    cur.close()
    conn.close()

    if not sorteio: return []

    dezenas_sorteadas = list(sorteio)
    analise_popularidade = []

    for n in dezenas_sorteadas:
        peso = 0
        # C-1: Números "Datas" (01 a 31) - Presentes na maioria das Quadras
        if 1 <= n <= 31: peso += 10
        # C-2: Números redondos ou da sorte (Finais 0 e 7)
        if n % 10 in [0, 7]: peso += 5
        # C-3: Números dobrados (11, 22, 33, 44, 55)
        if n in [11, 22, 33, 44, 55]: peso += 7
        
        analise_popularidade.append({"numero": n, "peso": peso})

    # Ordena para mostrar quais números do sorteio "carregaram" as Quadras/Quinas
    ranking = sorted(analise_popularidade, key=lambda x: x['peso'], reverse=True)
    return [item['numero'] for item in ranking]

def salvar_pesos_otimizados(config):
    """Salva a melhor configuração encontrada no banco de dados."""
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute("""
        UPDATE configuracao_pesos 
        SET peso_popularidade = %s, peso_sombra = %s, peso_momentum = %s, 
            peso_silencio = %s, ultima_atualizacao = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (config['pop'], config['som'], config['mom'], config['sil']))
    conn.commit()
    cur.close()
    conn.close()

def obter_pesos_cache():
    """Lê os pesos salvos no banco para carregamento instantâneo."""
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute("SELECT peso_popularidade, peso_sombra, peso_momentum, peso_silencio FROM configuracao_pesos WHERE id = 1")
    res = cur.fetchone()
    cur.close()
    conn.close()
    return {"pop": float(res[0]), "som": float(res[1]), "mom": float(res[2]), "sil": float(res[3])}

def processar_aprendizado_reforco():
    conn = conectar_banco()
    cur = conn.cursor()
    
    # 1. Pega o último sorteio real
    cur.execute("SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6 FROM sorteios ORDER BY concurso DESC LIMIT 1")
    ultimo_real = cur.fetchone()
    concurso_num = ultimo_real[0]
    gabarito = set(ultimo_real[1:])

    # 2. Busca a última previsão que a máquina fez para esse concurso
    cur.execute("SELECT dezenas_previstas, pesos_utilizados FROM historico_previsoes WHERE concurso_alvo = %s", (concurso_num,))
    previsao = cur.fetchone()

    if previsao:
        previstos = set(previsao[0])
        pesos_antigos = previsao[1]
        acertos = len(previstos.intersection(gabarito))
        
        # 3. LÓGICA DE AJUSTE (O "APRENDIZADO")
        # Se acertamos pouco (menos de 3), vamos forçar uma re-otimização agressiva
        # Se acertamos Quadra ou Quina, vamos "congelar" e dar bônus para esses pesos
        novo_ajuste_necessario = acertos < 4 

        if novo_ajuste_necessario:
            print(f"Acertos: {acertos}. Iniciando recalibragem para aprender com o erro...")
            # Chamamos a otimização aumentando o limite de busca (olhando mais para trás)
            otimizar_pesos_convergencia(limite_backtest=20) 
        else:
            print(f"Excelente performance ({acertos} acertos). Mantendo e reforçando pesos.")
            
    cur.close()
    conn.close()
    
def validar_palpite_elite(dezenas):
    """Verifica se o jogo respeita as constantes matemáticas da Mega-Sena."""
    # 1. Filtro de Soma (Intervalo de maior probabilidade)
    soma = sum(dezenas)
    if not (150 <= soma <= 220):
        return False

    # 2. Filtro de Paridade (Equilíbrio entre Pares e Ímpares)
    pares = len([n for n in dezenas if n % 2 == 0])
    if pares not in [2, 3, 4]: # Aceita proporções 2x4, 3x3 ou 4x2
        return False

    # 3. Filtro de Números Primos (Histórico de 1 a 2 por sorteio)
    primos_ref = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
    qtd_primos = len([n for n in dezenas if n in primos_ref])
    if qtd_primos not in [1, 2]:
        return False

    # 4. Filtro de Quadrantes (Distribuição no volante)
    q1 = q2 = q3 = q4 = 0
    for n in dezenas:
        coluna = (n - 1) % 10 + 1
        linha = (n - 1) // 10 + 1
        if linha <= 3 and coluna <= 5: q1 += 1
        elif linha <= 3 and coluna > 5: q2 += 1
        elif linha > 3 and coluna <= 5: q3 += 1
        else: q4 += 1
    
    # Evita que um único quadrante tenha mais de 3 números (concentração excessiva)
    if any(q > 3 for q in [q1, q2, q3, q4]):
        return False

    return True

def gerar_alta_convergencia_filtrada(pesos_final):
    """Gera o palpite de elite utilizando os pesos da IA e os filtros biométricos."""
    # Extrai as 12 melhores dezenas segundo a IA para criar combinações
    candidatos = [n for n, c in pesos_final.most_common(12)]
    
    # Testa combinações de 6 números entre as 12 melhores dezenas
    # O itertools.combinations garante que buscaremos a melhor harmonia estatística
    for combo in itertools.combinations(sorted(candidatos), 6):
        if validar_palpite_elite(combo):
            return list(combo)
            
    # Fallback de segurança: caso nenhuma combinação passe nos filtros rigorosos
    return [n for n, c in pesos_final.most_common(6)]

def obter_dezenas_pendentes_ciclo():
    """
    Rastreia o ciclo atual: identifica quais dezenas ainda não saíram 
    desde que o último ciclo de 60 números foi completado.
    """
    conn = conectar_banco()
    cur = conn.cursor()
    
    # Buscamos os sorteios do mais recente para o mais antigo
    cur.execute("SELECT bola1, bola2, bola3, bola4, bola5, bola6 FROM sorteios ORDER BY concurso DESC")
    sorteios = cur.fetchall()
    cur.close()
    conn.close()

    dezenas_encontradas = set()
    dezenas_pendentes = set(range(1, 61))

    # Vamos voltando no tempo até que tenhamos encontrado as 60 dezenas
    # ou até acabar o histórico (início de um novo ciclo)
    for s in sorteios:
        for bola in s:
            if bola in dezenas_pendentes:
                dezenas_pendentes.remove(bola)
        
        # Se as pendentes acabarem, significa que o ciclo fechou exatamente aqui
        # Mas queremos as pendentes do ciclo ATUAL, então paramos se o ciclo anterior fechar
        if len(dezenas_pendentes) == 0:
            break
            
    return list(dezenas_pendentes)

def calcular_peso_urgencia(dezenas_pendentes):
    """
    Atribui um bônus de peso para dezenas baseando-se na proximidade do fim do ciclo.
    Quanto menos números faltarem, maior o peso de cada um.
    """
    qtd_faltante = len(dezenas_pendentes)
    
    # Se faltarem muitos números, o peso é baixo. 
    # Se faltarem menos de 10, a "urgência" aumenta.
    if qtd_faltante == 0: return {}
    
    # Fórmula de Urgência: se faltam 5 números, cada um ganha 4.0 de peso extra.
    # Se faltam 30, ganham apenas 0.5.
    peso_bonus = max(0.5, 20.0 / qtd_faltante) if qtd_faltante < 15 else 0.5
    
    return {n: peso_bonus for n in dezenas_pendentes}

def classificar_cluster_sorteio(dezenas, acumulou):
    """
    Classifica o sorteio entre 'PADRAO' ou 'ZEBRA'.
    Baseia-se na conformidade com os filtros biométricos e resultado da Caixa.
    """
    soma = sum(dezenas)
    pares = len([n for n in dezenas if n % 2 == 0])
    
    # Critérios de Zebra:
    # 1. Soma fora do padrão (150-220)
    # 2. Paridade extrema (0P, 1P, 5P ou 6P)
    # 3. Acumulou (indício de dezenas pouco intuitivas)
    
    is_zebra = False
    if not (150 <= soma <= 220): is_zebra = True
    if pares not in [2, 3, 4]: is_zebra = True
    if acumulou: is_zebra = True # Reforço de comportamento caótico
    
    return "ZEBRA" if is_zebra else "PADRAO"

def atualizar_clusters_historicos():
    """Percorre o banco e classifica todos os sorteios existentes."""
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute("SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6, acumulou FROM sorteios")
    sorteios = cur.fetchall()
    
    for s in sorteios:
        tipo = classificar_cluster_sorteio(list(s[1:7]), s[7])
        cur.execute("UPDATE sorteios SET cluster_tipo = %s WHERE concurso = %s", (tipo, s[0]))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Clusters históricos atualizados com sucesso!")
    
def gerar_fusao_cibernetica(palpite_neural, palpite_ia_estatistico):
    """
    Versão 2.0: Foco em Resiliência. 
    Mantém o núcleo da Estatística Base e usa a IA para 
    refinar as dezenas de maior incerteza.
    """
    # 1. Identifica o Consenso (O que ambos concordam é Ouro)
    consenso = [n for n in palpite_neural if n in palpite_ia_estatistico]
    
    # 2. Começa preenchendo com o Consenso
    fusao = list(consenso)
    
    # 3. Adiciona as 3 dezenas mais Fortes da Estatística Base (que tem 0.63 de média)
    for n in palpite_ia_estatistico:
        if len(fusao) < 5 and n not in fusao:
            fusao.append(n)
            
    # 4. Usa a IA Neural para dar o "tiro de misericórdia" (a última dezena)
    for n in palpite_neural:
        if len(fusao) < 6 and n not in fusao:
            fusao.append(n)
            
    # 5. AJUSTE DE OURO: Se a IA e a Base escolheram números vizinhos (ex: 14 e 15)
    # o sistema agora prioriza o de maior frequência histórica para evitar jogos 'bobos'.
    fusao = sorted(list(set(fusao)))
    if len(fusao) > 6:
        fusao = fusao[:6]
        
    return fusao

def calcular_nivel_confianca(palpite_neural, palpite_estatistico):
    """
    Calcula a confiança baseada na interseção dos palpites.
    3+ números iguais = Alta
    2 números iguais = Média
    1 ou 0 = Baixa (Divergência técnica)
    """
    intersecao = len(set(palpite_neural).intersection(set(palpite_estatistico)))
    
    if intersecao >= 3:
        return {"nivel": "Alta", "cor": "text-green-500", "percentual": 85}
    elif intersecao == 2:
        return {"nivel": "Média", "cor": "text-yellow-500", "percentual": 60}
    else:
        return {"nivel": "Baixa", "cor": "text-red-500", "percentual": 35}