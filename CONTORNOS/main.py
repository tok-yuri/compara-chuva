import os
import json
from qgis.core import (
    QgsApplication,
    QgsGeometry,
    QgsLayerDefinition,
    QgsProject,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsWkbTypes,
)
import pandas as pd


prefix_path = os.environ.get("QGIS_PREFIX_PATH", "/usr")
QgsApplication.setPrefixPath(prefix_path, True)

qgs = QgsApplication([], False)
qgs.initQgis()

# Carregar JSON com códigos das bacias
def load_bacias_codigos():
    """Carrega o arquivo JSON com os códigos das bacias e items"""
    try:
        with open("./bacias_codigos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Arquivo bacias_codigos.json não encontrado")
        return {"bacias": []}

bacias_data = load_bacias_codigos()

# Criar dicionário de busca rápida: {nome_bacia: {nome_item: {codigo, id}}}
codigos_map = {}
for bacia in bacias_data.get("bacias", []):
    bacia_nome = bacia.get("nome")
    codigos_map[bacia_nome] = {}
    for item in bacia.get("items", []):
        item_nome = item.get("nome")
        codigo = item.get("codigo")
        item_id = item.get("id", "")
        if item_nome and codigo:
            codigos_map[bacia_nome][item_nome] = {"codigo": codigo, "id": item_id}

qlr_file = os.environ.get("QLR_FILE", "./Projeto_salvo2.qlr")
if not os.path.exists(qlr_file):
    raise FileNotFoundError(f"QLR file not found: {qlr_file}")

project = QgsProject.instance()
root = project.layerTreeRoot()
QgsLayerDefinition().loadLayerDefinition(qlr_file, project, root)
print("Camadas do QLR adicionadas ao projeto com sucesso.")

outputs: list[str] = []

def out(msg: str) -> None:
    print(msg)
    outputs.append(msg)

def print_root_groups() -> None:
    groups = [c for c in root.children() if isinstance(c, QgsLayerTreeGroup)]
    if not groups:
        out("Nenhum grupo encontrado em root.")
        return
    out("Grupos no root:")
    for g in groups:
        out(f"- {g.name()}")

def to_single_polygon(geom: QgsGeometry) -> QgsGeometry:
    if geom is None or geom.isEmpty():
        return geom
    if geom.type() != QgsWkbTypes.PolygonGeometry:
        return geom
    if not geom.isMultipart():
        return geom

    parts = geom.asMultiPolygon()
    if not parts:
        return geom

    biggest = None
    biggest_area = -1.0
    for part in parts:
        part_geom = QgsGeometry.fromPolygonXY(part)
        area = part_geom.area()
        if area > biggest_area:
            biggest_area = area
            biggest = part_geom
    return biggest if biggest else geom

def layer_wkt(layer) -> str:
    if layer is None:
        return ""
    geoms = []
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom and not geom.isEmpty():
            geoms.append(geom)
    if not geoms:
        return ""
    if len(geoms) == 1:
        return to_single_polygon(geoms[0]).asWkt()
    try:
        merged = QgsGeometry.unaryUnion(geoms)
        merged = to_single_polygon(merged)
        return merged.asWkt() if merged else ""
    except Exception:
        merged = geoms[0]
        for g in geoms[1:]:
            merged = merged.combine(g)
        merged = to_single_polygon(merged)
        return merged.asWkt() if merged else ""

def print_group_layers(group_name: str = "REMVIES") -> None:
    group = root.findGroup(group_name)
    if group is None:
        out(f"Grupo '{group_name}' não encontrado.")
        return

    out(f"Layers no grupo '{group_name}':")
    def walk(node, indent="", bacia_nome=""):
        for child in node.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                name = layer.name() if layer else child.name()
                # Buscar código e id no JSON
                codigo = ""
                if bacia_nome and bacia_nome in codigos_map:
                    info = codigos_map[bacia_nome].get(name, {})
                    codigo = info.get("codigo", "") if isinstance(info, dict) else info
                if codigo:
                    out(f"{indent}- {name}\t{codigo}")
                else:
                    out(f"{indent}- {name}")
            elif isinstance(child, QgsLayerTreeGroup):
                current_bacia = child.name()
                out(f"{indent}[{current_bacia}]")
                walk(child, indent + "  ", current_bacia)
    walk(group)

def export_group_contornos_wkt(group_name: str = "REMVIES", output_file: str = "./contornos_wkt.csv") -> None:
    group = root.findGroup(group_name)
    if group is None:
        out(f"Grupo '{group_name}' não encontrado para exportação.")
        return

    rows_ec45 = ["basin_name;ana_code;smap_basin_id;geometry"]
    rows_outros = ["basin_name;ana_code;smap_basin_id;geometry"]

    def walk(node, bacia_nome=""):
        for child in node.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                name = layer.name() if layer else child.name()
                codigo = ""
                item_id = ""
                if bacia_nome and bacia_nome in codigos_map:
                    info = codigos_map[bacia_nome].get(name, {})
                    if isinstance(info, dict):
                        codigo = info.get("codigo", "")
                        item_id = info.get("id", "")
                    else:
                        codigo = info
                wkt = layer_wkt(layer)
                # Separar por nome começando com EC45-
                if name.startswith("EC45-"):
                    row = f"{name};{item_id};{wkt}"
                    rows_ec45.append(row)
                else:
                    row = f"{name};{codigo};{item_id};{wkt}"
                    rows_outros.append(row)
            elif isinstance(child, QgsLayerTreeGroup):
                walk(child, child.name())

    walk(group)

    # Salvar arquivo EC45
    ec45_file = output_file.replace(".csv", "_ec45.csv")
    with open(ec45_file, "w", encoding="utf-8") as f:
        f.write("\n".join(rows_ec45).replace('Polygon', 'POLYGON'))
    print(f"Arquivo WKT EC45 salvo em {ec45_file}")
    
    # Salvar arquivo outros
    outros_file = output_file.replace(".csv", "_outros.csv")
    with open(outros_file, "w", encoding="utf-8") as f:
        f.write("\n".join(rows_outros).replace('Polygon', 'POLYGON'))
    print(f"Arquivo WKT outros salvo em {outros_file}")


print_root_groups()
print_group_layers("REMVIES")
export_group_contornos_wkt("REMVIES", "./contornos_wkt.csv")
# Salvar resultados em arquivo de exportação
pd.read_csv("./contornos_wkt_outros.csv", sep=";").to_parquet("./contornos_wkt_outros.parquet")

export_file = "./exported_layers.txt"
if export_file:
    with open(export_file, "w", encoding="utf-8") as f:
        f.write("\n".join(outputs))
    print(f"Resultado salvo em {export_file}")

qgs.exitQgis()




