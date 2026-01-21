import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from main import conectar_banco

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Cache the model
_cached_model = None
_cached_scaler = None

def preparar_dados():
    conn = conectar_banco()
    df = pd.read_sql("SELECT bola1, bola2, bola3, bola4, bola5, bola6 FROM sorteios ORDER BY concurso ASC", conn)
    conn.close()

    if len(df) < 20:
        return None, None, None

    scaler = MinMaxScaler()
    dados_norm = scaler.fit_transform(df)

    X = dados_norm[:-1] # Entrada: Sorteio atual
    y = dados_norm[1:]  # Saída: Próximo sorteio
    
    return X, y, scaler

def prever_proximo_sorteio():
    global _cached_model, _cached_scaler
    X, y, scaler = preparar_dados()
    
    if X is None:
        return [1, 2, 3, 4, 5, 6] # Fallback caso não haja dados suficientes

    if _cached_model is None:
        # Criando uma Rede Neural MLP (Multi-Layer Perceptron)
        # 3 camadas escondidas com 100 neurônios cada
        _cached_model = MLPRegressor(
            hidden_layer_sizes=(200, 100, 50), # Camadas mais profundas
            activation='relu',                 # Melhor que logistic para este caso
            solver='adam',                     # Mais robusto que lbfgs
            max_iter=2000,
            random_state=42
        )

        _cached_model.fit(X, y)
        _cached_scaler = scaler

    # Pegamos o último sorteio real para prever o próximo
    ultimo_sorteio = y[-1].reshape(1, -1)
    previsao_norm = _cached_model.predict(ultimo_sorteio)
    
    # Desnormalizar
    resultado = _cached_scaler.inverse_transform(previsao_norm)
    
    # Tratar os números para o formato Mega-Sena
    palpite = np.round(resultado[0]).astype(int)
    palpite = [max(1, min(60, n)) for n in palpite] # Garante entre 1 e 60
    
    # Garantir números únicos
    palpite_final = []
    for n in sorted(palpite):
        while n in palpite_final or n < 1 or n > 60:
            n = (n % 60) + 1
        palpite_final.append(n)
        
    return sorted(palpite_final)