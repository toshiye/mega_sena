import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def conectar_banco():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )

def migrar_dados(caminho_csv):
    try:
        conn = conectar_banco()
        cur = conn.cursor()

        # Lendo o CSV
        df = pd.read_csv("resultados.csv", dtype=str)
        df.columns = df.columns.str.strip()

        # Query de inserção otimizada (usando a estrutura de SMALLINT que criamos)
        insert_query = """
        INSERT INTO sorteios (concurso, data_sorteio, bola1, bola2, bola3, bola4, bola5, bola6)
        VALUES (%s, TO_DATE(%s, 'DD/MM/YYYY'), %s, %s, %s, %s, %s, %s)
        ON CONFLICT (concurso) DO NOTHING;
        """

        for _, linha in df.iterrows():
            cur.execute(insert_query, (
                int(linha['Concurso']),
                linha['Data'],
                int(linha['bola 1']),
                int(linha['bola 2']),
                int(linha['bola 3']),
                int(linha['bola 4']),
                int(linha['bola 5']),
                int(linha['bola 6'])
            ))

        conn.commit()
        print(f"Sucesso: {len(df)} registros processados.")

    except Exception as e:
        print(f"Erro na migração: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    migrar_dados("resultados.csv")