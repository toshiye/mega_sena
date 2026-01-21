import json
from collections import Counter
import pandas as pd
from main import (
    conectar_banco, 
    otimizar_pesos_convergencia, 
    obter_analise_sql,
    obter_dezenas_por_popularidade,
    obter_matriz_vizinhanca_historica,
    obter_dezenas_momentum,
    gerar_alta_convergencia_filtrada,
    ZONAS_SILENCIOSAS,
    validar_palpite_elite
)

def executar_simulacao_completa(qtd_concursos=50):
    """
    Executa uma simulação retroativa (Backtest) para validar a eficácia da IA.
    Retorna os dados formatados para o Dashboard.
    """
    conn = conectar_banco()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6 
        FROM sorteios 
        ORDER BY concurso DESC LIMIT %s
    """, (qtd_concursos,))
    
    sorteios = cur.fetchall()[::-1] 
    
    print(f"🚀 Iniciando Stress Test nos últimos {len(sorteios)} concursos...")
    log_performance = []

    for i in range(len(sorteios) - 1):
        conc_alvo = int(sorteios[i+1][0]) # Garante int puro
        gabarito = set(sorteios[i+1][1:])
        
        config = otimizar_pesos_convergencia(limite_backtest=10)
        
        pesos_final = Counter()
        for n in obter_dezenas_por_popularidade(top=15): pesos_final[n] += config["pop"]
        for n in obter_matriz_vizinhanca_historica(top=10): pesos_final[n] += config["som"]
        for n in ZONAS_SILENCIOSAS: pesos_final[n] += config["sil"]
        for n in obter_dezenas_momentum(): pesos_final[n] += config["mom"]
        
        palpite = gerar_alta_convergencia_filtrada(pesos_final)
        
        acertos = len(set(palpite).intersection(gabarito))
        passou_filtros = validar_palpite_elite(palpite)
        
        # O USO DO int() AQUI EVITA O ERRO 500 NA API
        log_performance.append({
            "concurso": int(conc_alvo),
            "acertos": int(acertos),
            "filtros": "OK" if passou_filtros else "FALHA"
        })
        
        print(f"Simulado Concurso {conc_alvo}: {acertos} acertos | Filtros: {'✅' if passou_filtros else '❌'}")

    cur.close()
    conn.close()

    df = pd.DataFrame(log_performance)
    
    media = float(df['acertos'].mean()) if not df.empty else 0.0
    quadras = int(len(df[df['acertos'] == 4]))
    quinas = int(len(df[df['acertos'] == 5]))
    senas = int(len(df[df['acertos'] == 6]))

    print("\n" + "="*40)
    print(f"📊 STRESS TEST CONCLUÍDO: Média {media:.2f} | Quadras: {quadras}")
    print("="*40)

    try:
        conn_audit = conectar_banco()
        cur_audit = conn_audit.cursor()
        conformidade = (len(df[df['filtros'] == 'OK']) / len(df)) * 100 if not df.empty else 0
        
        cur_audit.execute("""
            INSERT INTO auditoria_stress 
            (qtd_concursos, media_acertos, total_quadras, total_quinas, total_senas, conformidade_filtros, historico_detalhado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            len(df), media, quadras, quinas, senas, conformidade, 
            json.dumps(log_performance)
        ))
        
        conn_audit.commit()
        cur_audit.close()
        conn_audit.close()
    except Exception as e:
        print(f"❌ Erro ao salvar auditoria: {e}")

    return {
        "status": "success",
        "media_acertos": media,
        "total_quadras": quadras,
        "total_quinas": quinas,
        "total_senas": senas,
        "historico": log_performance
    }