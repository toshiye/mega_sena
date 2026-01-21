import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def sincronizar_caixa():
    url = "https://loteriascaixa-api.herokuapp.com/api/megasena/latest"
    try:
        dados = requests.get(url).json()
        
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cur = conn.cursor()

        query = """
        INSERT INTO sorteios (
            concurso, data_sorteio, bola1, bola2, bola3, bola4, bola5, bola6,
            ganhadores_sena, ganhadores_quina, ganhadores_quadra,
            valor_estimado_proximo, acumulou
        ) VALUES (%s, TO_DATE(%s, 'DD/MM/YYYY'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (concurso) DO UPDATE SET
            ganhadores_sena = EXCLUDED.ganhadores_sena,
            ganhadores_quina = EXCLUDED.ganhadores_quina,
            ganhadores_quadra = EXCLUDED.ganhadores_quadra;
        """

        cur.execute(query, (
            dados['concurso'], dados['data'],
            int(dados['dezenas'][0]), int(dados['dezenas'][1]), int(dados['dezenas'][2]),
            int(dados['dezenas'][3]), int(dados['dezenas'][4]), int(dados['dezenas'][5]),
            dados['premiacoes'][0]['ganhadores'], 
            dados['premiacoes'][1]['ganhadores'],
            dados['premiacoes'][2]['ganhadores'],
            dados['valorEstimadoProximoConcurso'],
            dados['acumulou']
        ))

        conn.commit()
        print(f"Sucesso! Concurso {dados['concurso']} sincronizado.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro na sincronização: {e}")

if __name__ == "__main__":
    sincronizar_caixa()