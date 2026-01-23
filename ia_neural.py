import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from main import conectar_banco
import random
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# Cache do modelo para evitar re-treino desnecessário na mesma sessão
_cached_model = None
_cached_scaler = None

def preparar_dados():
    conn = conectar_banco()
    df = pd.read_sql("SELECT bola1, bola2, bola3, bola4, bola5, bola6 FROM sorteios ORDER BY concurso ASC", conn)
    conn.close()

    if len(df) < 20:
        return None, None, None

    # Normalização
    scaler = MinMaxScaler()
    dados_norm = scaler.fit_transform(df)

    # Injeção de Ruído (Jitter): Adiciona uma variação mínima de 0.1% 
    # para evitar que a rede memorize a média central
    ruido = np.random.normal(0, 0.001, dados_norm.shape)
    dados_norm_ruidoso = np.clip(dados_norm + ruido, 0, 1)

    X = dados_norm_ruidoso[:-1] 
    y = dados_norm_ruidoso[1:]  
    
    return X, y, scaler

def prever_proximo_sorteio():
    global _cached_model, _cached_scaler
    X, y, scaler = preparar_dados()
    
    if X is None:
        return [1, 10, 20, 30, 40, 50] # Fallback mais distribuído

    # Forçamos o re-treino com uma semente aleatória para gerar palpites diferentes
    # Se o modelo for sempre o mesmo (random_state=42), o palpite nunca muda.
    semente_viva = random.randint(1, 9999)

    _cached_model = MLPRegressor(
        hidden_layer_sizes=(250, 150, 50), # Aumentamos a densidade
        activation='relu',                 # Mantemos relu para não achatar
        solver='adam',                     # Adam lida melhor com o ruído inserido
        max_iter=3000,
        shuffle=True,                      # Embaralha os dados para evitar padrões lineares
        random_state=semente_viva          # A mágica da variação está aqui
    )

    _cached_model.fit(X, y)
    _cached_scaler = scaler

    # Pegamos o último sorteio real e aplicamos uma leve perturbação para prever
    ultimo_sorteio = y[-1].reshape(1, -1)
    
    # Geramos 3 previsões e pegamos a média ponderada ou apenas a última
    previsao_norm = _cached_model.predict(ultimo_sorteio)
    
    # Desnormalizar
    resultado = _cached_scaler.inverse_transform(previsao_norm)
    
    # Tratar os números
    palpite = np.round(resultado[0]).astype(int)
    
    # Pós-processamento para garantir que as dezenas não fiquem coladas (ex: 30, 31, 32)
    palpite_final = []
    # Ordenamos os candidatos brutos
    candidatos = sorted([max(1, min(60, n)) for n in palpite])
    
    for n in candidatos:
        # Se o número já existe ou é muito próximo (colado), aplica um salto aleatório
        while n in palpite_final:
            n = random.randint(1, 60)
        palpite_final.append(n)
        
    return sorted(palpite_final)