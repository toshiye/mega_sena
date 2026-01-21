from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
# ADICIONADO: importação da função de simulação
from main import (
    processar_todas_estrategias, 
    simular_performance, 
    conectar_banco,
    gerar_fusao_cibernetica,
    calcular_nivel_confianca 
)

from pydantic import BaseModel
from datetime import date

import psycopg2
import psycopg2.extras

import subprocess

import stress_test

from ia_neural import prever_proximo_sorteio
from testar_ia import stress_test_neural_v2

app = FastAPI(title="Mega-Sena Meta-Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/palpites")
async def get_palpites():
    try:
        # 1. Coleta dados brutos
        dados = processar_todas_estrategias()
        palpite_neural = prever_proximo_sorteio()
        
        # 2. Converte tipos NumPy para Python Puro (Essencial para evitar Erro 500)
        p_neural_puro = [int(n) for n in palpite_neural]
        p_base_puro = [int(n) for n in dados["meta"]["Alta Convergência"]]
        
        # 3. Gera a Fusão e Confiança
        palpite_fusao = gerar_fusao_cibernetica(p_neural_puro, p_base_puro)
        confianca = calcular_nivel_confianca(p_neural_puro, p_base_puro)
        
        # 4. Organiza o dicionário de saída (Mesmos nomes que o index.html espera)
        dados["meta"]["Predição IA (Neural MLP)"] = p_neural_puro
        dados["meta"]["Sinergia Cibernética (Fusão)"] = palpite_fusao
        
        # Injeta a confiança no debug_ia para o frontend
        dados["debug_ia"]["confianca"] = confianca
        
        return {
            "status": "sucesso",
            "estrategias_base": dados["base"],
            "meta_analise": dados["meta"],
            "debug_ia": dados["debug_ia"]
        }
    except Exception as e:
        print(f"ERRO CRÍTICO NA API: {e}")
        return {"status": "erro", "mensagem": str(e)}

class SorteioSchema(BaseModel):
    concurso: int
    data: date
    bolas: list[int]

@app.post("/api/sorteios")
async def adicionar_sorteio(dados: SorteioSchema):
    try:        
        conn = conectar_banco()
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO sorteios (concurso, data_sorteio, bola1, bola2, bola3, bola4, bola5, bola6)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (concurso) DO NOTHING;
        """
        
        cur.execute(insert_query, (
            dados.concurso, dados.data,
            dados.bolas[0], dados.bolas[1], dados.bolas[2],
            dados.bolas[3], dados.bolas[4], dados.bolas[5]
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "sucesso", "mensagem": f"Concurso {dados.concurso} adicionado!"}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
    
@app.get("/api/dashboard")
async def get_dashboard_stats():
    try:
        conn = conectar_banco()
        cur = conn.cursor()

        cur.execute("SELECT numero, concursos_de_atraso FROM v_atraso_numeros ORDER BY concursos_de_atraso DESC LIMIT 10;")
        atraso_data = cur.fetchall()

        cur.execute("SELECT numero, COUNT(*) FROM v_frequencia_numeros GROUP BY numero ORDER BY COUNT DESC LIMIT 10;")
        freq_data = cur.fetchall()

        cur.close()
        conn.close()

        return {
            "atraso": {
                "labels": [f"Nº {n[0]}" for n in atraso_data], 
                "data": [n[1] for n in atraso_data] 
            },
            "frequencia": {
                "labels": [f"Nº {n[0]}" for n in freq_data], 
                "data": [n[1] for n in freq_data] 
            }
        }
    except Exception as e:
        return {"erro": str(e)}
    
@app.get("/api/simulacao")
async def get_simulacao(tipo: str = "favoritos"):
    try:
        dados_analise = processar_todas_estrategias()
        # Ajuste para os novos nomes das chaves
        if tipo == "favoritos":
            palpite = dados_analise["meta"]["Favoritos do Grupo"]
        elif tipo == "recentes":
            palpite = dados_analise["base"]["Tendência Recente"]
        else:
            palpite = dados_analise["meta"]["Alta Convergência"] # Mudado para Alta Convergência como "Misto"

        resultados = simular_performance(palpite)
        return {
            "labels": [f"C-{r['concurso']}" for r in resultados],
            "acertos": [r["acertos"] for r in resultados],
            "resumo": {
                "quadras": len([r for r in resultados if r["acertos"] == 4]),
                "quinas": len([r for r in resultados if r["acertos"] == 5]),
                "senas": len([r for r in resultados if r["acertos"] == 6])
            }
        }
    except Exception as e:
        return {"erro": str(e)}
    
@app.get("/api/ranking")
async def get_ranking():
    try:
        dados = processar_todas_estrategias()
        # Unificamos todas as estratégias em um único dicionário para testar
        todas_estrategias = {**dados["base"], **dados["meta"]}
        
        ranking = []
        
        for nome, palpite in todas_estrategias.items():
            resultados = simular_performance(palpite)
            total_acertos = sum([r["acertos"] for r in resultados])
            quadras = len([r for r in resultados if r["acertos"] == 4])
            
            ranking.append({
                "estrategia": nome,
                "pontuacao_total": total_acertos,
                "quadras": quadras,
                "palpite": palpite
            })
            
        # Ordena pelo maior número de acertos totais
        ranking = sorted(ranking, key=lambda x: x["pontuacao_total"], reverse=True)
        
        return ranking[:3] # Retorna apenas o Top 3
    except Exception as e:
        return {"erro": str(e)}
    
@app.get("/api/ultimo-resumo")
async def get_ultimo_resumo():
    try:
        conn = conectar_banco()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) # Retorna como dicionário
        
        cur.execute("""
            SELECT concurso, data_sorteio, bola1, bola2, bola3, bola4, bola5, bola6,
                   ganhadores_sena, ganhadores_quina, ganhadores_quadra, 
                   valor_estimado_proximo, acumulou
            FROM sorteios ORDER BY concurso DESC LIMIT 1
        """)
        resumo = cur.fetchone()
        cur.close()
        conn.close()
        return resumo
    except Exception as e:
        return {"erro": str(e)}
    
@app.get("/api/estimativa-satelite/{concurso}")
async def get_estimativa_satelite(concurso: int):
    try:
        from main import analisar_ancoras_sorteio
        numeros = analisar_ancoras_sorteio(concurso)
        # Retornamos as 6 dezenas ordenadas pela probabilidade de acerto popular
        return {"concurso": concurso, "ancoras_provaveis": numeros}
    except Exception as e:
        return {"erro": str(e)}
    
@app.post("/api/sync-data")
async def sync_data():
    try:
        # 1. Roda o sync.py para baixar o sorteio mais recente da Caixa
        subprocess.run(["python", "sync.py"], check=True)
        
        # 2. Importa as ferramentas de inteligência do main.py
        from main import (
            conectar_banco, 
            processar_aprendizado_reforco, 
            processar_matriz_afinidade, 
            otimizar_pesos_convergencia,
            processar_todas_estrategias
        )
        
        # 3. APRENDIZADO: A máquina olha o que previu e compara com o que saiu
        # Ela ajusta a sensibilidade se houve erro no concurso anterior
        processar_aprendizado_reforco()
        
        # 4. ATUALIZAÇÃO ESTATÍSTICA: Recalcula Afinidades e Popularidade
        processar_matriz_afinidade()
        
        # 5. CALIBRAGEM: Roda o Backtest com foco em Quadra/Quina/Sena
        config_otimizada = otimizar_pesos_convergencia()
        
        # 6. REGISTRO DE FUTURO: Salva o novo palpite para conferir no próximo sync
        # Isso cria a 'memória' para o aprendizado do próximo sorteio
        dados_novos = processar_todas_estrategias()
        palpite_ia = dados_novos["meta"]["Alta Convergência"]
        
        # Pega o próximo número de concurso (último + 1)
        conn = conectar_banco()
        cur = conn.cursor()
        cur.execute("SELECT MAX(concurso) FROM sorteios")
        ultimo_concurso = cur.fetchone()[0]
        proximo_concurso = ultimo_concurso + 1
        
        # Salva na tabela de histórico para a máquina conferir depois
        import json
        cur.execute("""
            INSERT INTO historico_previsoes (concurso_alvo, dezenas_previstas, pesos_utilizados)
            VALUES (%s, %s, %s)
        """, (proximo_concurso, palpite_ia, json.dumps(config_otimizada)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Sincronizado! A máquina analisou o concurso {ultimo_concurso}, recalibrou os pesos e já projetou o concurso {proximo_concurso}."
        }
    except Exception as e:
        return {"status": "error", "message": f"Falha no ciclo de aprendizado: {str(e)}"}
    
@app.get("/api/auditoria-ia")
async def get_auditoria_ia():
    try:
        conn = conectar_banco()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT DISTINCT ON (h.concurso_alvo) 
                   h.concurso_alvo, h.dezenas_previstas, h.pesos_utilizados,
                   s.bola1, s.bola2, s.bola3, s.bola4, s.bola5, s.bola6
            FROM historico_previsoes h
            LEFT JOIN sorteios s ON h.concurso_alvo = s.concurso
            ORDER BY h.concurso_alvo DESC LIMIT 2
        """)
        dados = cur.fetchall()
        
        primos_ref = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
        relatorio = []

        def calcular_metadados(nums):
            if not nums or any(n is None for n in nums) or sum(nums) == 0:
                return None
            soma = sum(nums)
            pares = len([n for n in nums if n % 2 == 0])
            primos = len([n for n in nums if n in primos_ref])
            return {"soma": soma, "paridade": f"{pares}P/{6-pares}I", "primos": primos}

        for d in dados:
            real_nums = [d['bola1'], d['bola2'], d['bola3'], d['bola4'], d['bola5'], d['bola6']]
            tem_resultado = all(v is not None for v in real_nums)
            previstos = d['dezenas_previstas']
            
            acertos_lista = list(set(previstos).intersection(set(real_nums))) if tem_resultado else []
            
            relatorio.append({
                "concurso": d['concurso_alvo'],
                "real": real_nums if tem_resultado else [0,0,0,0,0,0],
                "previsto": previstos,
                "acertos": acertos_lista,
                "porcentagem": round((len(acertos_lista) / 6) * 100, 1) if tem_resultado else 0,
                "faixa": "SENA!" if len(acertos_lista) == 6 else "QUINA!" if len(acertos_lista) == 5 else "QUADRA!" if len(acertos_lista) == 4 else "Terno" if len(acertos_lista) == 3 else "Nenhuma",
                "tem_resultado": tem_resultado,
                "meta_ia": calcular_metadados(previstos),
                "meta_real": calcular_metadados(real_nums) if tem_resultado else None,
                "pesos": d['pesos_utilizados']
            })
            
        cur.close()
        conn.close()
        return relatorio
    except Exception as e:
        return {"erro": str(e)}
    
@app.post("/api/sync-data")
async def sync_data():
    try:
        # 1. Download de dados novos
        subprocess.run(["python", "sync.py"], check=True)
        
        from main import (
            conectar_banco, 
            processar_aprendizado_reforco, 
            processar_matriz_afinidade, 
            otimizar_pesos_convergencia,
            obter_analise_sql,
            obter_dezenas_por_popularidade,
            obter_matriz_vizinhanca_historica,
            obter_dezenas_momentum,
            gerar_alta_convergencia_filtrada,
            ZONAS_SILENCIOSAS
        )
        from collections import Counter
        import json

        # 2. Aprendizado com o erro do sorteio que acabou de sair
        processar_aprendizado_reforco()
        
        # 3. Atualização das tabelas de suporte
        processar_matriz_afinidade()
        
        # 4. Calibragem de Pesos (Backtest focado em Quadra/Quina)
        config = otimizar_pesos_convergencia()
        
        # 5. GERAÇÃO DO PALPITE DE ELITE FILTRADO
        hist, _, _ = obter_analise_sql()
        pesos_final = Counter()
        
        # Aplicamos a mesma lógica de camadas do processar_todas_estrategias
        for n in obter_dezenas_por_popularidade(top=15): pesos_final[n] += config["pop"]
        for n in obter_matriz_vizinhanca_historica(top=10): pesos_final[n] += config["som"]
        for n in ZONAS_SILENCIOSAS: pesos_final[n] += config["sil"]
        for n in obter_dezenas_momentum(): pesos_final[n] += config["mom"]
        
        # AQUI ESTÁ A MUDANÇA: O palpite agora é filtrado pelas novas variáveis
        palpite_ia_filtrado = gerar_alta_convergencia_filtrada(pesos_final)
        
        # 6. Registro do Futuro na Tabela de Auditoria
        conn = conectar_banco()
        cur = conn.cursor()
        cur.execute("SELECT MAX(concurso) FROM sorteios")
        proximo_concurso = cur.fetchone()[0] + 1
        
        cur.execute("""
            INSERT INTO historico_previsoes (concurso_alvo, dezenas_previstas, pesos_utilizados)
            VALUES (%s, %s, %s)
            ON CONFLICT (concurso_alvo) DO UPDATE SET 
                dezenas_previstas = EXCLUDED.dezenas_previstas,
                pesos_utilizados = EXCLUDED.pesos_utilizados;
        """, (proximo_concurso, palpite_ia_filtrado, json.dumps(config)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "message": "Ciclo completo de IA concluído com filtros de elite!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/api/executar-stress-test")
async def rodar_stress():
    try:
        # Chamamos a função de processamento que você já validou no console
        # Ela deve retornar um dicionário com os resultados
        resultados = stress_test.executar_simulacao_completa(qtd_concursos=50)
        return resultados
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/api/historico-stress")
async def obter_historico_stress():
    try:
        conn = conectar_banco()
        cur = conn.cursor()
        cur.execute("""
            SELECT data_execucao, media_acertos, total_quadras, total_quinas, total_senas
            FROM auditoria_stress 
            ORDER BY data_execucao DESC LIMIT 5
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        historico = []
        for r in rows:
            historico.append({
                "data": r[0].strftime("%d/%m %H:%M"),
                "media": float(r[1]),
                "premios": f"QD:{r[2]} | QN:{r[3]} | SN:{r[4]}"
            })
        return historico
    except Exception as e:
        return []
    
@app.get("/api/comparativo-ia-base")
async def get_comparativo_ia():
    try:
        # Rodamos o teste nos últimos 15 concursos para não pesar o carregamento
        resultados = stress_test_neural_v2(n_concursos=15)
        
        # Formatamos para o Chart.js
        return {
            "labels": [f"C-{r['concurso']}" for r in reversed(resultados)],
            "acertos_ia": [r['neural'] for r in reversed(resultados)],
            "media_base": [r['base'] for r in reversed(resultados)]
        }
    except Exception as e:
        return {"erro": str(e)}
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)