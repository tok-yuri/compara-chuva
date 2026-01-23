# Guia Rápido de Uso - Comparação de Precipitação

## Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/tok-yuri/compara-chuva.git
cd compara-chuva

# Instale as dependências
pip install -r requirements.txt

# Inicie o Jupyter Notebook
jupyter notebook
```

## Uso com Dados de Exemplo

O repositório já inclui dados de exemplo para testar o notebook:

1. Abra `compara_chuva.ipynb` no Jupyter Notebook
2. Na célula de configuração (Seção 1), os parâmetros já estão ajustados para os dados de exemplo:
   ```python
   nome_modelo = "MODELO_EXEMPLO"
   horizonte = 7
   data_rodada = "20260123"
   diretorio_base = "dados_exemplo"
   ```
3. Execute todas as células: `Cell > Run All`
4. Os resultados serão salvos em: `dados_exemplo/MODELO_EXEMPLO/20260123/comparacao/`

## Uso com Seus Dados

### 1. Organize seus arquivos

Crie a seguinte estrutura de diretórios:

```
/seus_dados/
└── {NOME_DO_MODELO}/
    └── {DATA_RODADA}/
        ├── ONS/
        │   └── dados.csv  (ou .xlsx, .parquet)
        └── TOK/
            └── dados.csv  (ou .xlsx, .parquet)
```

### 2. Formate seus dados

Seus arquivos CSV/Excel/Parquet devem ter pelo menos estas colunas:
- `ponto` (ou equivalente: local, estacao, id)
- `data` (ou equivalente: date, datetime)
- `precipitacao_mm` (ou equivalente: chuva, mm, precip)

Exemplo de CSV:
```csv
ponto,data,precipitacao_mm
Ponto_01,2026-01-01,15.5
Ponto_01,2026-01-02,22.3
Ponto_02,2026-01-01,18.7
...
```

### 3. Configure o notebook

Ajuste os parâmetros na Seção 1 do notebook:

```python
nome_modelo = "GFS"              # Nome do seu modelo
horizonte = 10                   # Horizonte de previsão
data_rodada = "20260125"         # Data da rodada (YYYYMMDD)
diretorio_base = "/seus_dados"   # Caminho para seus dados
```

### 4. Execute o notebook

Execute todas as células e os resultados serão salvos em:
```
/seus_dados/GFS/20260125/comparacao/
```

## Outputs Gerados

O notebook gera 9 tipos de arquivos:

### Tabelas (CSV)
1. `estatisticas_por_ponto_*.csv` - Estatísticas completas
2. `acumulados_diferencas_*.csv` - Acumulados positivos/negativos
3. `desvio_padrao_diferencas_*.csv` - Desvio padrão por ponto
4. `matriz_diferencas_*.csv` - Matriz de diferenças

### Visualizações (PNG)
5. `heatmap_diferencas_*.png` - Heatmap principal
6. `heatmap_diferencas_absolutas_*.png` - Heatmap absoluto
7. `graficos_acumulados_*.png` - Gráficos de barras
8. `distribuicao_diferencas_*.png` - Histograma e boxplot

### Relatório (TXT)
9. `relatorio_consolidado_*.txt` - Relatório textual completo

## Teste Rápido

Execute o script de teste para validar a instalação:

```bash
python test_notebook.py
```

Deve exibir:
```
================================================================================
TESTE CONCLUÍDO COM SUCESSO! ✓
================================================================================
```

## Interpretação dos Resultados

### Diferenças Positivas
- Valores > 0: ONS registrou **mais** chuva que TOK
- Aparecem em **vermelho** nos heatmaps

### Diferenças Negativas
- Valores < 0: ONS registrou **menos** chuva que TOK
- Aparecem em **azul** nos heatmaps

### Desvio Padrão Alto
- Indica **maior variabilidade** entre as fontes
- Sugere menor consistência nos dados

## Troubleshooting

### Erro: "Nenhum arquivo de dados encontrado"
- Verifique a estrutura de diretórios
- Confirme que os arquivos estão nos formatos suportados (.csv, .xlsx, .parquet)

### Erro: "KeyError: 'precipitacao_mm'"
- Renomeie as colunas no seu arquivo fonte, ou
- Modifique a função `padronizar_dataframe()` no notebook

### Gráficos não aparecem
- Execute: `%matplotlib inline` no início do notebook
- Verifique se matplotlib está instalado

## Personalização

### Adicionar novos cálculos
Edite a Seção 5 do notebook para adicionar novos cálculos de diferenças.

### Modificar visualizações
Ajuste os parâmetros dos gráficos nas Seções 9-12.

### Exportar para outros formatos
Adicione código para salvar em Excel, PDF, etc.:
```python
# Excel
stats_por_ponto.to_excel(caminho_output / "estatisticas.xlsx")

# Parquet
dados_comparacao.to_parquet(caminho_output / "dados.parquet")
```

## Dicas

✓ **Execute célula por célula** na primeira vez para entender o fluxo
✓ **Salve o notebook** após executar para preservar os outputs
✓ **Use dados de exemplo** primeiro para testar modificações
✓ **Documente suas alterações** se modificar o notebook

## Suporte

Para problemas ou dúvidas:
1. Verifique a documentação completa no README.md
2. Execute o teste: `python test_notebook.py`
3. Abra uma issue no GitHub com detalhes do erro
