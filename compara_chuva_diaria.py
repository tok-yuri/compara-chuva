#!/usr/bin/env python3
"""Compara precipitação diária entre ONS e TOK para a pasta COMPARAR_CHUVA_DIARIA.

Uso mínimo:
    python compara_chuva_diaria.py

Opções:
    --base-dir   Diretório base com subpastas ONS/ e TOK/ (padrão: COMPARAR_CHUVA_DIARIA)
    --date       (opcional) subpasta de data dentro do base-dir
    --horizonte  horizonte em dias (apenas para gerar dados de exemplo)
"""
from pathlib import Path
import re
import pandas as pd
import numpy as np
import argparse


def carregar_base_estacoes(caminho: Path) -> pd.DataFrame:
    estacoes = pd.read_csv(caminho)
    if 'ana_code' in estacoes.columns:
        estacoes['ponto'] = estacoes['ana_code']
    elif 'smap_basin_id' in estacoes.columns:
        estacoes['ponto'] = estacoes['smap_basin_id'].astype(str)
    else:
        estacoes['ponto'] = estacoes.index.astype(str)
    estacoes['lat_round'] = estacoes['lat'].round(2)
    estacoes['lon_round'] = estacoes['lon'].round(2)
    return estacoes[['ponto', 'lat_round', 'lon_round']]


def extrair_data_arquivo(nome_arquivo: str) -> pd.Timestamp | None:
    base = Path(nome_arquivo).stem
    try:
        token = base.split('_')[-1].split('a')[-1].split('.')[0]
        if len(token) != 6:
            return None
        return pd.to_datetime(token, format='%d%m%y')
    except Exception:
        return None


def montar_df_arquivo_dat(arquivo: Path, estacoes: pd.DataFrame) -> pd.DataFrame:
    data = pd.read_csv(
        arquivo,
        sep=r'\s+',
        header=None,
        names=['lon', 'lat', 'precipitacao_mm']
    )
    data['lat_round'] = data['lat'].round(2)
    data['lon_round'] = data['lon'].round(2)
    data = data.merge(estacoes, on=['lat_round', 'lon_round'], how='left')
    data['ponto'] = data['ponto'].fillna(
        data['lat_round'].astype(str) + ',' + data['lon_round'].astype(str)
    )

    data_arquivo = extrair_data_arquivo(arquivo.name)
    if data_arquivo is None:
        return pd.DataFrame(columns=['ponto', 'data', 'precipitacao_mm'])

    data['data'] = data_arquivo
    return data[['ponto', 'data', 'precipitacao_mm']]


def carregar_dados_fonte(caminho: Path, fonte: str, estacoes: pd.DataFrame) -> pd.DataFrame:
    """Carrega todos os arquivos .dat da subpasta e concatena em um DataFrame."""
    arquivos = sorted(caminho.glob("*.dat"))
    if not arquivos:
        print(f"Nenhum arquivo .dat encontrado em {caminho} para {fonte}")
        return pd.DataFrame(columns=['ponto', 'data', 'precipitacao_mm'])

    frames = []
    for arquivo in arquivos:
        df = montar_df_arquivo_dat(arquivo, estacoes)
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame(columns=['ponto', 'data', 'precipitacao_mm'])

    return pd.concat(frames, ignore_index=True)


def gerar_dados_exemplo(fonte: str, horizonte: int = 45) -> pd.DataFrame:
    np.random.seed(42 if fonte == "ONS" else 43)
    pontos = [f"Ponto_{i:02d}" for i in range(1, 21)]
    datas = pd.date_range(start=pd.Timestamp.today().normalize(), periods=horizonte, freq='D')
    rows = []
    for p in pontos:
        for d in datas:
            precip = np.random.gamma(2, 10) if fonte == "ONS" else np.random.gamma(2.2, 9.5)
            rows.append({'ponto': p, 'data': d, 'precipitacao_mm': precip})
    return pd.DataFrame(rows)


def padronizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    lower = [c.lower() for c in df2.columns]
    rename = {}
    for c, cl in zip(df2.columns, lower):
        if 'ponto' in cl or 'estacao' in cl or 'local' in cl:
            rename[c] = 'ponto'
        elif 'data' in cl or 'date' in cl:
            rename[c] = 'data'
        elif 'precip' in cl or 'chuva' in cl or 'mm' in cl:
            rename[c] = 'precipitacao_mm'
    if rename:
        df2 = df2.rename(columns=rename)
    if 'data' in df2.columns:
        df2['data'] = pd.to_datetime(df2['data'])
    return df2


def comparar(dados_ons: pd.DataFrame, dados_tok: pd.DataFrame, caminho_output: Path, data_label: str):
    dados_ons = padronizar_dataframe(dados_ons)
    dados_tok = padronizar_dataframe(dados_tok)

    dados_comparados = dados_tok.pivot(index='ponto', columns="data", values="precipitacao_mm") - dados_ons.pivot(index='ponto', columns="data", values="precipitacao_mm")

    dados = pd.merge(dados_ons, dados_tok, on=['ponto', 'data'], how='outer', suffixes=('_ons', '_tok'))
    dados = dados.fillna(0)
    dados['diferenca'] = dados['precipitacao_mm_tok'] - dados['precipitacao_mm_ons']
    dados['diferenca_abs'] = dados['diferenca'].abs()
    dados['diferenca_pct'] = np.where(dados['precipitacao_mm_ons'] != 0,
                                      dados['diferenca'] / dados['precipitacao_mm_ons'] * 100, 0)

    caminho_output.mkdir(parents=True, exist_ok=True)
    (caminho_output / f"comparacao_{data_label}.csv").write_text(dados.to_csv(index=False, float_format='%.2f'))

    # Estatísticas por ponto
    stats = dados.groupby('ponto').agg({
        'precipitacao_mm_ons': ['mean', 'sum'],
        'precipitacao_mm_tok': ['mean', 'sum'],
        'diferenca': ['mean', 'sum', 'std']
    }).round(2)
    stats.columns = ['ONS_media', 'ONS_total', 'TOK_media', 'TOK_total', 'Dif_media', 'Dif_total', 'Dif_std']
    stats.to_csv(caminho_output / f"estatisticas_por_ponto_{data_label}.csv")

    # Acumulados
    dif_pos = dados[dados['diferenca'] > 0].groupby('ponto')['diferenca'].sum()
    dif_neg = dados[dados['diferenca'] < 0].groupby('ponto')['diferenca'].sum()
    acumulados = pd.DataFrame({
        'Acumulado_Positivo_mm': dif_pos,
        'Acumulado_Negativo_mm': dif_neg,
    }).fillna(0).round(2)
    acumulados['Total_Liquido_mm'] = acumulados['Acumulado_Positivo_mm'] + acumulados['Acumulado_Negativo_mm']
    acumulados.to_csv(caminho_output / f"acumulados_{data_label}.csv", float_format='%.2f')
    dados_comparados.to_csv(caminho_output / f"comparacao_matriz_{data_label}.csv", float_format='%.2f')

    print(f"Resultados salvos em: {caminho_output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-dir', default='COMPARAR_CHUVA_DIARIA', help='Diretório base com ONS/ e TOK/')
    parser.add_argument('--date', default=None, help='(opcional) subpasta de data')
    parser.add_argument('--horizonte', type=int, default=43)
    args = parser.parse_args()

    base = Path(args.base_dir)
    if args.date:
        base = base / args.date
    
    print(f"Usando diretório base: {base}")

    caminho_ons = base / 'ONS'
    caminho_tok = base / 'TOK'
    if not caminho_ons.exists() or not caminho_tok.exists():
        print('Aviso: pastas ONS/TOK não encontradas no caminho especificado:', base)

    caminho_output = base / 'Output'
    estacoes_path = Path(__file__).resolve().parent / 'base_de_estacoes.csv'
    estacoes = carregar_base_estacoes(estacoes_path)

    ons_pastas = {}
    for pasta in caminho_ons.iterdir() if caminho_ons.exists() else []:
        if pasta.is_dir():
            match = re.search(r'(\d+)$', pasta.name)
            if match:
                ons_pastas[int(match.group(1))] = pasta

    tok_pastas = {}
    for pasta in caminho_tok.iterdir() if caminho_tok.exists() else []:
        if pasta.is_dir():
            match = re.search(r'c(\d+)$', pasta.name, re.IGNORECASE)
            if match:
                tok_pastas[int(match.group(1))] = pasta

    for tok_num in sorted(tok_pastas.keys()):
        ons_num = tok_num - 1
        if ons_num not in ons_pastas:
            print(f"Sem pasta ONS equivalente para TOK c{tok_num}")
            continue

        pasta_ons = ons_pastas[ons_num]
        pasta_tok = tok_pastas[tok_num]
        print(f"Comparando {pasta_ons.name} vs {pasta_tok.name}")

        dados_ons = carregar_dados_fonte(pasta_ons, 'ONS', estacoes)
        dados_tok = carregar_dados_fonte(pasta_tok, 'TOK', estacoes)

        if dados_ons.empty:
            print(f"Dados ONS insuficientes em {pasta_ons.name}")
            continue
        if dados_tok.empty:
            print(f"Dados TOK insuficientes em {pasta_tok.name}")
            continue

        data_label = f"{pasta_ons.name}_vs_{pasta_tok.name}"
        comparar(dados_ons, dados_tok, caminho_output, data_label)


if __name__ == '__main__':
    main()
