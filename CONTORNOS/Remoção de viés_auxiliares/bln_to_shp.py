#!/usr/bin/env python3
"""
Script para converter arquivos .bln em .shp

Percorre recursivamente as pastas contornos_genericos/ e ETA40/,
lê arquivos .bln, valida o formato e converte para shapefile.

Validações:
- Remove terceira coluna se existir (mantém apenas longitude, latitude)
- Verifica se primeira linha = número de coordenadas
- Fecha polígonos automaticamente se necessário
- Preserva arquivos originais (não modifica)
"""

import os
import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_bln_file(filepath):
    """
    Lê e processa um arquivo .bln
    
    Args:
        filepath: Caminho para o arquivo .bln
        
    Returns:
        tuple: (coordenadas, metadados) ou (None, None) em caso de erro
        coordenadas: lista de tuplas (lon, lat)
        metadados: dict com informações do processamento
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filtrar linhas vazias
        lines = [line for line in lines if line.strip()]
        
        if len(lines) < 2:
            logger.error(f"{filepath}: Arquivo vazio ou inválido (apenas {len(lines)} linha(s))")
            return None, None
        
        # Processar primeira linha
        first_line = lines[0].strip()
        
        # Tentar extrair número de pontos (pode ter flag após vírgula)
        if ',' in first_line:
            num_points_str = first_line.split(',')[0].strip()
        else:
            num_points_str = first_line.strip()
        
        try:
            expected_points = int(num_points_str)
        except ValueError:
            logger.error(f"{filepath}: Primeira linha inválida: '{first_line}'")
            return None, None
        
        # Processar coordenadas (linhas 1 em diante)
        coords = []
        for i, line in enumerate(lines[1:], start=2):
            line = line.strip()
            if not line:
                continue
            
            # Separar por vírgula
            parts = [p.strip() for p in line.split(',')]
            
            if len(parts) < 2:
                logger.warning(f"{filepath}: Linha {i} inválida: '{line}'")
                continue
            
            # Pegar apenas longitude e latitude (ignora terceira coluna se existir)
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                coords.append((lon, lat))
            except (ValueError, IndexError) as e:
                logger.warning(f"{filepath}: Erro ao processar linha {i}: {e}")
                continue
        
        if len(coords) < 3:
            logger.error(f"{filepath}: Polígono precisa de pelo menos 3 pontos, encontrado {len(coords)}")
            return None, None
        
        # Remover pontos duplicados consecutivos (exceto o último que fecha o polígono)
        original_count = len(coords)
        cleaned_coords = [coords[0]]  # Sempre manter o primeiro ponto
        
        for i in range(1, len(coords)):
            # Se não for o último ponto OU se for diferente do anterior, adicionar
            if i == len(coords) - 1 or coords[i] != coords[i-1]:
                cleaned_coords.append(coords[i])
        
        removed_duplicates = original_count - len(cleaned_coords)
        if removed_duplicates > 0:
            logger.info(f"{filepath}: Removidos {removed_duplicates} ponto(s) duplicado(s)")
            coords = cleaned_coords
        
        # Validar número de pontos
        actual_points = len(coords)
        metadados = {
            'expected_points': expected_points,
            'actual_points': actual_points,
            'points_match': expected_points == actual_points,
            'was_closed': False,
            'removed_duplicates': removed_duplicates,
            'had_extra_column': any(',' in line and len(line.split(',')) > 2 for line in lines[1:] if line.strip())
        }
        
        # Fechar polígono se necessário
        if coords[0] != coords[-1]:
            coords.append(coords[0])
            metadados['was_closed'] = True
            logger.info(f"{filepath}: Polígono fechado automaticamente")
        
        # Reportar discrepância no número de pontos
        if not metadados['points_match']:
            logger.warning(
                f"{filepath}: Esperado {expected_points} pontos, "
                f"encontrado {actual_points} (diferença: {actual_points - expected_points})"
            )
        
        return coords, metadados
        
    except Exception as e:
        logger.error(f"{filepath}: Erro ao processar arquivo: {e}")
        return None, None


def create_shapefile(coords, output_path, source_file):
    """
    Cria um shapefile a partir das coordenadas
    
    Args:
        coords: Lista de tuplas (lon, lat)
        output_path: Caminho para salvar o shapefile
        source_file: Nome do arquivo original (.bln)
    """
    try:
        # Criar polígono
        polygon = Polygon(coords)
        
        # Criar GeoDataFrame
        gdf = gpd.GeoDataFrame(
            {'name': [source_file], 'geometry': [polygon]},
            crs='EPSG:4326'  # WGS84
        )
        
        # Criar diretório se não existir
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar shapefile
        gdf.to_file(output_path, driver='ESRI Shapefile')
        logger.info(f"✓ Criado: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar shapefile {output_path}: {e}")
        return False


def main():
    """Função principal"""
    # Diretório base (onde está o script)
    base_dir = Path(__file__).parent
    
    # Diretório de saída
    output_dir = base_dir / 'output'
    
    logger.info("=" * 70)
    logger.info("CONVERSOR DE ARQUIVOS .BLN PARA .SHP")
    logger.info("=" * 70)
    logger.info(f"\nBuscando arquivos .bln em: {base_dir}")
    
    # Buscar todos os arquivos .bln recursivamente no diretório base
    bln_files = list(base_dir.rglob('*.bln'))
    
    # Filtrar arquivos dentro da pasta output (para não processar arquivos já convertidos)
    bln_files = [f for f in bln_files if 'output' not in f.parts]
    
    if not bln_files:
        logger.warning(f"\nNenhum arquivo .bln encontrado em {base_dir}")
        return 1
    
    logger.info(f"Encontrados {len(bln_files)} arquivo(s) .bln")
    
    # Estatísticas
    stats = {
        'total': 0,
        'success': 0,
        'errors': 0,
        'closed': 0,
        'extra_columns': 0,
        'point_mismatches': 0,
        'removed_duplicates': 0,
        'error_files': [],  # Lista de arquivos com erros
        'mismatch_files': [],  # Lista de arquivos com discrepância de pontos
        'closed_files': [],  # Lista de polígonos fechados
        'extra_column_files': [],  # Lista de arquivos com coluna extra
        'duplicate_files': []  # Lista de arquivos com pontos duplicados removidos
    }
    
    # Processar cada arquivo .bln encontrado
    for idx, bln_file in enumerate(bln_files, 1):
        stats['total'] += 1
        
        # Calcular caminho relativo ao diretório base
        rel_path = bln_file.relative_to(base_dir)
        
        # Criar caminho de saída mantendo estrutura
        output_path = output_dir / rel_path.with_suffix('.shp')
        
        logger.info(f"\nProcessando [{idx}]: {rel_path}")
        
        # Processar arquivo .bln
        coords, metadados = parse_bln_file(bln_file)
        
        if coords is None:
            stats['errors'] += 1
            stats['error_files'].append(str(rel_path))
            continue
        
        # Acumular estatísticas
        if metadados:
            if metadados['was_closed']:
                stats['closed'] += 1
                stats['closed_files'].append(str(rel_path))
            if metadados['had_extra_column']:
                stats['extra_columns'] += 1
                stats['extra_column_files'].append(str(rel_path))
            if metadados['removed_duplicates'] > 0:
                stats['removed_duplicates'] += metadados['removed_duplicates']
                stats['duplicate_files'].append({
                    'file': str(rel_path),
                    'count': metadados['removed_duplicates']
                })
            if not metadados['points_match']:
                stats['point_mismatches'] += 1
                stats['mismatch_files'].append({
                    'file': str(rel_path),
                    'expected': metadados['expected_points'],
                    'actual': metadados['actual_points']
                })
        
        # Criar shapefile
        if create_shapefile(coords, output_path, bln_file.name):
            stats['success'] += 1
        else:
            stats['errors'] += 1
            if str(rel_path) not in stats['error_files']:
                stats['error_files'].append(str(rel_path))
    
    # Relatório final
    logger.info("\n" + "=" * 70)
    logger.info("RELATÓRIO FINAL")
    logger.info("=" * 70)
    logger.info(f"Total de arquivos processados: {stats['total']}")
    logger.info(f"  ✓ Convertidos com sucesso: {stats['success']}")
    logger.info(f"  ✗ Erros: {stats['errors']}")
    logger.info(f"\nAjustes realizados:")
    logger.info(f"  • Polígonos fechados automaticamente: {stats['closed']}")
    logger.info(f"  • Pontos duplicados removidos: {stats['removed_duplicates']}")
    logger.info(f"  • Arquivos com coluna extra removida: {stats['extra_columns']}")
    logger.info(f"  • Arquivos com discrepância no número de pontos: {stats['point_mismatches']}")
    
    # Detalhamento de erros
    if stats['error_files']:
        logger.info("\n" + "-" * 70)
        logger.info(f"ARQUIVOS COM ERRO ({len(stats['error_files'])}):")
        logger.info("-" * 70)
        for i, file in enumerate(stats['error_files'], 1):
            logger.error(f"  {i}. {file}")
    
    # Detalhamento de discrepâncias
    if stats['mismatch_files']:
        logger.info("\n" + "-" * 70)
        logger.info(f"ARQUIVOS COM DISCREPÂNCIA NO NÚMERO DE PONTOS ({len(stats['mismatch_files'])}):")
        logger.info("-" * 70)
        for i, item in enumerate(stats['mismatch_files'], 1):
            diff = item['actual'] - item['expected']
            logger.warning(
                f"  {i}. {item['file']}\n"
                f"      Esperado: {item['expected']} | Encontrado: {item['actual']} | Diferença: {diff:+d}"
            )
    
    # Detalhamento de polígonos fechados
    if stats['closed_files'] and stats['closed'] > 0:
        logger.info("\n" + "-" * 70)
        logger.info(f"POLÍGONOS FECHADOS AUTOMATICAMENTE ({len(stats['closed_files'])}):")
        logger.info("-" * 70)
        # Mostrar apenas os primeiros 10 para não poluir muito
        for i, file in enumerate(stats['closed_files'][:10], 1):
            logger.info(f"  {i}. {file}")
        if len(stats['closed_files']) > 10:
            logger.info(f"  ... e mais {len(stats['closed_files']) - 10} arquivo(s)")
    
    # Detalhamento de pontos duplicados removidos
    if stats['duplicate_files']:
        logger.info("\n" + "-" * 70)
        logger.info(f"ARQUIVOS COM PONTOS DUPLICADOS REMOVIDOS ({len(stats['duplicate_files'])}):")
        logger.info("-" * 70)
        for i, item in enumerate(stats['duplicate_files'][:20], 1):
            logger.info(f"  {i}. {item['file']} - {item['count']} ponto(s)")
        if len(stats['duplicate_files']) > 20:
            logger.info(f"  ... e mais {len(stats['duplicate_files']) - 20} arquivo(s)")
    
    logger.info("\n" + "=" * 70)
    
    if stats['errors'] > 0:
        logger.warning(f"\n⚠ {stats['errors']} arquivo(s) com erro. Verifique a lista acima.")
        return 1
    
    logger.info(f"\n✓ Conversão concluída! Arquivos salvos em: {output_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
