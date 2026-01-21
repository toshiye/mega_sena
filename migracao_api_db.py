import requests
import psycopg2
import time
from main import conectar_banco

def migrar_historico_completo():
    # A API permite buscar todos os resultados de uma vez ou um por um
    # Vamos buscar o último concurso primeiro para saber o limite
    url_base = "https://loteriascaixa-api.herokuapp.com/api/megasena"
    
    print("Iniciando migração massiva... Aguarde.")
    try:
        response = requests.get(url_base)
        todos_sorteios = response.json()
        
        conn = conectar_banco()
        cur = conn.cursor()

        for dados in todos_sorteios:
            query = """
            INSERT INTO sorteios (
                concurso, data_sorteio, bola1, bola2, bola3, bola4, bola5, bola6,
                ganhadores_sena, ganhadores_quina, ganhadores_quadra, acumulou
            ) VALUES (%s, TO_DATE(%s, 'DD/MM/YYYY'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (concurso) DO UPDATE SET
                ganhadores_sena = EXCLUDED.ganhadores_sena,
                ganhadores_quina = EXCLUDED.ganhadores_quina,
                ganhadores_quadra = EXCLUDED.ganhadores_quadra;
            """
            # Tratamento básico para dezenas (garantir que são inteiros)
            dezenas = [int(n) for n in dados['dezenas']]
            
            cur.execute(query, (
                dados['concurso'], dados['data'],
                dezenas[0], dezenas[1], dezenas[2],
                dezenas[3], dezenas[4], dezenas[5],
                dados['premiacoes'][0]['ganhadores'], 
                dados['premiacoes'][1]['ganhadores'],
                dados['premiacoes'][2]['ganhadores'],
                dados['acumulou']
            ))
        
        conn.commit()
        print(f"Migração concluída! {len(todos_sorteios)} concursos salvos.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro na migração: {e}")

if __name__ == "__main__":
    migrar_historico_completo()