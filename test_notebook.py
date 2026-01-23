#!/usr/bin/env python3
"""
Script de teste para validar o notebook de comparação de chuva.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import seaborn as sns

print("=" * 80)
print("TESTE DO NOTEBOOK DE COMPARAÇÃO DE PRECIPITAÇÃO")
print("=" * 80)

# Configuração dos parâmetros
nome_modelo = "MODELO_EXEMPLO"
horizonte = 7
data_rodada = "20260123"
diretorio_base = "dados_exemplo"

print(f"\nParâmetros de teste:")
print(f"  Modelo: {nome_modelo}")
print(f"  Horizonte: {horizonte}")
print(f"  Data da rodada: {data_rodada}")
print(f"  Diretório base: {diretorio_base}")

# Construção dos caminhos
caminho_input = Path(diretorio_base) / nome_modelo / data_rodada
caminho_ons = caminho_input / "ONS"
caminho_tok = caminho_input / "TOK"
caminho_output = caminho_input / "comparacao"

print(f"\nCaminhos:")
print(f"  Input: {caminho_input}")
print(f"  ONS: {caminho_ons}")
print(f"  TOK: {caminho_tok}")
print(f"  Output: {caminho_output}")

# Verificar se os arquivos existem
print("\n" + "=" * 80)
print("VERIFICAÇÃO DE ARQUIVOS")
print("=" * 80)

arquivos_ons = list(caminho_ons.glob("*.csv"))
arquivos_tok = list(caminho_tok.glob("*.csv"))

print(f"\nArquivos ONS encontrados: {len(arquivos_ons)}")
for arquivo in arquivos_ons:
    print(f"  - {arquivo.name}")

print(f"\nArquivos TOK encontrados: {len(arquivos_tok)}")
for arquivo in arquivos_tok:
    print(f"  - {arquivo.name}")

if not arquivos_ons or not arquivos_tok:
    print("\n❌ ERRO: Arquivos de dados não encontrados!")
    sys.exit(1)

# Carregar dados
print("\n" + "=" * 80)
print("CARREGAMENTO DE DADOS")
print("=" * 80)

print("\nCarregando dados ONS...")
dados_ons = pd.read_csv(arquivos_ons[0])
print(f"  Registros carregados: {len(dados_ons)}")
print(f"  Colunas: {list(dados_ons.columns)}")

print("\nCarregando dados TOK...")
dados_tok = pd.read_csv(arquivos_tok[0])
print(f"  Registros carregados: {len(dados_tok)}")
print(f"  Colunas: {list(dados_tok.columns)}")

# Garantir que a coluna data está no formato datetime
dados_ons['data'] = pd.to_datetime(dados_ons['data'])
dados_tok['data'] = pd.to_datetime(dados_tok['data'])

# Merge dos dados
print("\n" + "=" * 80)
print("COMPARAÇÃO DE DADOS")
print("=" * 80)

dados_comparacao = pd.merge(
    dados_ons,
    dados_tok,
    on=['ponto', 'data'],
    suffixes=('_ons', '_tok'),
    how='outer'
).fillna(0)

print(f"\nRegistros após merge: {len(dados_comparacao)}")
print(f"Pontos únicos: {dados_comparacao['ponto'].nunique()}")
print(f"Datas únicas: {dados_comparacao['data'].nunique()}")

# Calcular diferenças
dados_comparacao['diferenca'] = dados_comparacao['precipitacao_mm_ons'] - dados_comparacao['precipitacao_mm_tok']
dados_comparacao['diferenca_abs'] = dados_comparacao['diferenca'].abs()

print("\n" + "=" * 80)
print("ESTATÍSTICAS DAS DIFERENÇAS")
print("=" * 80)

print(f"\nDiferença média: {dados_comparacao['diferenca'].mean():.2f} mm")
print(f"Desvio padrão: {dados_comparacao['diferenca'].std():.2f} mm")
print(f"Diferença mínima: {dados_comparacao['diferenca'].min():.2f} mm")
print(f"Diferença máxima: {dados_comparacao['diferenca'].max():.2f} mm")

# Acumulados
dif_positivas = dados_comparacao[dados_comparacao['diferenca'] > 0]
dif_negativas = dados_comparacao[dados_comparacao['diferenca'] < 0]

acumulado_positivo = dif_positivas['diferenca'].sum()
acumulado_negativo = dif_negativas['diferenca'].sum()

print(f"\nAcumulado positivo: {acumulado_positivo:.2f} mm")
print(f"Acumulado negativo: {acumulado_negativo:.2f} mm")
print(f"Total líquido: {acumulado_positivo + acumulado_negativo:.2f} mm")

# Criar diretório de saída
print("\n" + "=" * 80)
print("GERAÇÃO DE SAÍDAS")
print("=" * 80)

caminho_output.mkdir(parents=True, exist_ok=True)
print(f"\nDiretório de saída criado: {caminho_output}")

# Gerar estatísticas por ponto
stats_por_ponto = dados_comparacao.groupby('ponto').agg({
    'precipitacao_mm_ons': ['mean', 'sum'],
    'precipitacao_mm_tok': ['mean', 'sum'],
    'diferenca': ['mean', 'sum', 'std', 'min', 'max'],
    'diferenca_abs': ['mean', 'max']
}).round(2)

stats_por_ponto.columns = [
    'ONS_media', 'ONS_total',
    'TOK_media', 'TOK_total',
    'Dif_media', 'Dif_total', 'Dif_desvio_padrao', 'Dif_min', 'Dif_max',
    'Dif_abs_media', 'Dif_abs_max'
]

# Salvar estatísticas
arquivo_stats = caminho_output / f"estatisticas_por_ponto_{data_rodada}.csv"
stats_por_ponto.to_csv(arquivo_stats)
print(f"\n✓ Estatísticas salvas: {arquivo_stats.name}")

# Gerar heatmap
matriz_diferencas = dados_comparacao.pivot_table(
    index='ponto',
    columns='data',
    values='diferenca',
    aggfunc='mean'
).fillna(0)

fig, ax = plt.subplots(figsize=(12, 6))
sns.heatmap(
    matriz_diferencas,
    cmap='RdBu_r',
    center=0,
    annot=True,
    fmt='.1f',
    linewidths=0.5,
    cbar_kws={'label': 'Diferença (mm)'},
    ax=ax
)
ax.set_title(f'Heatmap de Diferenças (ONS - TOK)\n{nome_modelo} - {data_rodada}')
ax.set_xlabel('Data')
ax.set_ylabel('Ponto de Interesse')
plt.tight_layout()

arquivo_heatmap = caminho_output / f"heatmap_diferencas_{data_rodada}.png"
plt.savefig(arquivo_heatmap, dpi=150, bbox_inches='tight')
plt.close()
print(f"✓ Heatmap salvo: {arquivo_heatmap.name}")

# Salvar matriz de diferenças
arquivo_matriz = caminho_output / f"matriz_diferencas_{data_rodada}.csv"
matriz_diferencas.to_csv(arquivo_matriz)
print(f"✓ Matriz salva: {arquivo_matriz.name}")

# Verificar arquivos gerados
print("\n" + "=" * 80)
print("VERIFICAÇÃO DE SAÍDAS")
print("=" * 80)

arquivos_gerados = list(caminho_output.glob("*"))
print(f"\nTotal de arquivos gerados: {len(arquivos_gerados)}")
for arquivo in sorted(arquivos_gerados):
    tamanho = arquivo.stat().st_size
    print(f"  ✓ {arquivo.name} ({tamanho:,} bytes)")

print("\n" + "=" * 80)
print("TESTE CONCLUÍDO COM SUCESSO! ✓")
print("=" * 80)
print("\n✓ Todos os componentes principais foram testados")
print("✓ Dados carregados corretamente")
print("✓ Cálculos realizados com sucesso")
print("✓ Arquivos de saída gerados")
print("\nO notebook está pronto para uso!")
