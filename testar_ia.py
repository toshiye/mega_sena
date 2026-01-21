import pandas as pd
import numpy as np
import warnings
from ia_neural import prever_proximo_sorteio
from main import conectar_banco, processar_todas_estrategias, gerar_fusao_cibernetica

warnings.filterwarnings("ignore", category=UserWarning)

def stress_test_neural_v2(n_concursos=15):
    conn = conectar_banco()
    df_validacao = pd.read_sql(f"SELECT * FROM sorteios ORDER BY concurso DESC LIMIT {n_concursos}", conn)
    conn.close()
    
    resultados = []
    print(f"🚀 Iniciando Batalha de Inteligências (IA vs Base vs FUSÃO) - {n_concursos} concursos...")

    for index, linha in df_validacao.iterrows():
        concurso_alvo = linha['concurso']
        sorteio_real = set([linha['bola1'], linha['bola2'], linha['bola3'], linha['bola4'], linha['bola5'], linha['bola6']])
        
        # 1. Palpite Neural Puro
        palpite_neural = prever_proximo_sorteio()
        acertos_neural = len(set(palpite_neural).intersection(sorteio_real))
        
        # 2. Média das Estratégias Base
        dados_estatisticos = processar_todas_estrategias()
        acertos_base = []
        for numeros in dados_estatisticos['base'].values():
            acertos_base.append(len(set(numeros).intersection(sorteio_real)))
        media_base = np.mean(acertos_base)
        
        # 3. A FUSÃO (O novo motor)
        palpite_fusao = gerar_fusao_cibernetica(palpite_neural, dados_estatisticos["meta"]["Alta Convergência"])
        acertos_fusao = len(set(palpite_fusao).intersection(sorteio_real))
        
        resultados.append({
            "concurso": concurso_alvo,
            "neural": acertos_neural,
            "base": media_base,
            "fusao": acertos_fusao
        })
        
        # Log visual para acompanhar
        status = "🔥 FUSÃO VENCEU!" if acertos_fusao > acertos_neural and acertos_fusao > media_base else "OK"
        print(f"C-{concurso_alvo} | Neural: {acertos_neural} | Base: {media_base:.2f} | FUSÃO: {acertos_fusao} -> {status}")

    df = pd.DataFrame(resultados)
    print("\n" + "="*40)
    print("🏆 PLACAR FINAL (MÉDIAS)")
    print(f"🧠 IA Neural Pura:  {df['neural'].mean():.2f}")
    print(f"📊 Estatística Base: {df['base'].mean():.2f}")
    print(f"⚡ Sinergia (Fusão): {df['fusao'].mean():.2f}")
    print("="*40)

    return resultados

if __name__ == "__main__":
    stress_test_neural_v2(15)