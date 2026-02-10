#!/usr/bin/env python3
"""
Script para comparar dados de hindcast ONS vs TOK
Mapeia dados TOK (smap_basin_id) com dados ONS (estações com lat/lon)
Gera arquivo de saída com apenas lat, lon e valores de comparação
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurações
ONS_DIR = Path('/media/HD/PROJETOS/GITHUB/compara-chuva/COMPARAR_HINDCAST/ONS')
TOK_DIR = Path('/media/HD/PROJETOS/GITHUB/compara-chuva/COMPARAR_HINDCAST/TOK')
ESTACOES_FILE = Path('/media/HD/PROJETOS/GITHUB/compara-chuva/base_de_estacoes.csv')
OUTPUT_DIR = Path('/media/HD/PROJETOS/GITHUB/compara-chuva/COMPARACAO_HINDCAST')

# Criar diretório de saída
OUTPUT_DIR.mkdir(exist_ok=True)

def load_estacoes():
    """Carrega arquivo de estações e cria mapping smap_basin_id -> lat/lon"""
    estacoes = pd.read_csv(ESTACOES_FILE)
    # Criar dicionário: smap_basin_id -> (lat, lon, ana_code)
    mapping = {}
    for _, row in estacoes.iterrows():
        basin_id = int(row['smap_basin_id'])
        mapping[basin_id] = {
            'lat': row['lat'],
            'lon': row['lon'],
            'ana_code': row['ana_code']
        }
    return mapping

def parse_ons_file(filepath):
    """
    Lê arquivo ONS (whitespace-separated)
    Retorna DataFrame com: [estacao, lat, lon, valores...]
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) > 3:
                estacao = parts[0]
                lat = float(parts[1])
                lon = float(parts[2])
                valores = np.array([float(x) for x in parts[3:]], dtype=np.float32)
                data.append({
                    'estacao': estacao,
                    'lat': lat,
                    'lon': lon,
                    'valores': valores
                })
    return data

def parse_tok_file(filepath):
    """
    Lê arquivo TOK (CSV)
    Retorna dicionário: {smap_basin_id -> valores}
    """
    df = pd.read_csv(filepath)
    # Primeira coluna é smap_basin_id
    basin_ids = df.iloc[:, 0].values
    # Resto são os valores
    valores_array = df.iloc[:, 1:].values
    
    data = {}
    for idx, basin_id in enumerate(basin_ids):
        basin_int = int(float(basin_id))
        data[basin_int] = valores_array[idx].astype(np.float32)
    
    return data

def compare_hindcasts(ons_data, tok_data, estacoes_mapping, prefix_p):
    """
    Compara dados ONS com TOK
    Retorna DataFrame com: [lat, lon, estacao, diferenca_media, rmse, correlacao]
    """
    resultados = []
    
    # Para cada estação ONS
    for ons_station in ons_data:
        estacao = ons_station['estacao']
        lat = ons_station['lat']
        lon = ons_station['lon']
        ons_valores = ons_station['valores']
        
        # Encontrar correspondência no arquivo TOK
        # A correspondência é feita por posição/ordem na lista
        station_idx = ons_data.index(ons_station)
        
        # TOK tem basin IDs 1-11, deve haver correspondência
        # Vamos procurar o basin_id que melhor corresponde
        best_match = None
        best_distance = float('inf')
        
        for basin_id, tok_valores in tok_data.items():
            # Pegar coordenadas do basin_id
            if basin_id in estacoes_mapping:
                mapping_info = estacoes_mapping[basin_id]
                basin_lat = mapping_info['lat']
                basin_lon = mapping_info['lon']
                
                # Calcular distância
                distance = np.sqrt((lat - basin_lat)**2 + (lon - basin_lon)**2)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = (basin_id, tok_valores, basin_lat, basin_lon)
        
        if best_match is not None:
            basin_id, tok_valores, basin_lat, basin_lon = best_match
            
            # Calcular estatísticas
            # Usar o menor tamanho para evitar erros
            min_len = min(len(ons_valores), len(tok_valores))
            ons_sub = ons_valores[:min_len]
            tok_sub = tok_valores[:min_len]
            
            # Diferença média
            diff_media = np.mean(np.abs(ons_sub - tok_sub))
            
            # RMSE
            rmse = np.sqrt(np.mean((ons_sub - tok_sub)**2))
            
            # Correlação
            if np.std(ons_sub) > 0 and np.std(tok_sub) > 0:
                correlacao = np.corrcoef(ons_sub, tok_sub)[0, 1]
            else:
                correlacao = np.nan
            
            resultados.append({
                'lat': lat,
                'lon': lon,
                'estacao_ons': estacao,
                'basin_id_tok': basin_id,
                'estacao_tok': estacoes_mapping[basin_id]['ana_code'],
                'diferenca_media': diff_media,
                'rmse': rmse,
                'correlacao': correlacao,
                'distancia_km': best_distance
            })
    
    return pd.DataFrame(resultados)

def main():
    print("=== Comparação de Hindcast ONS vs TOK ===\n")
    
    # Carregar mapping de estações
    print("1. Carregando arquivo base_de_estacoes.csv...")
    estacoes_mapping = load_estacoes()
    print(f"   - Encontrados {len(estacoes_mapping)} basin IDs\n")
    
    # Processar cada arquivo pX
    for p in range(102):
        print(f"2.{p} Processando arquivo p{p}...")
        
        ons_file = ONS_DIR / f'ECMWFf_m_210126_p{p}.dat'
        tok_file = TOK_DIR / f'EC45_m{p}.csv'
        output_file = OUTPUT_DIR / f'comparacao_p{p}.csv'
        
        if not ons_file.exists():
            print(f"   ✗ Arquivo ONS não encontrado: {ons_file}")
            continue
        
        if not tok_file.exists():
            print(f"   ✗ Arquivo TOK não encontrado: {tok_file}")
            continue
        
        try:
            # Parsear arquivos
            print(f"   - Lendo arquivo ONS...")
            ons_data = parse_ons_file(ons_file)
            print(f"     {len(ons_data)} estações encontradas")
            
            print(f"   - Lendo arquivo TOK...")
            tok_data = parse_tok_file(tok_file)
            print(f"     {len(tok_data)} basins encontrados")
            
            # Comparar
            print(f"   - Comparando dados...")
            comparacao = compare_hindcasts(ons_data, tok_data, estacoes_mapping, f'p{p}')
            
            # Selecionar apenas lat e lon para saída, conforme requisito
            output_df = comparacao[['lat', 'lon', 'estacao_ons', 'estacao_tok', 
                                    'diferenca_media', 'rmse', 'correlacao', 'distancia_km']]
            
            # Salvar
            output_df.sort_values(by='diferenca_media', inplace=True, ascending=False)
            output_df.to_csv(output_file, index=False, float_format='%.2f')
            print(f"   ✓ Arquivo de comparação salvo: {output_file}")
            print(f"     {len(output_df)} linhas de comparação\n")
            
        except Exception as e:
            print(f"   ✗ Erro ao processar p{p}: {str(e)}\n")
    
    print("=== Comparação Concluída ===")
    print(f"Arquivos salvos em: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
