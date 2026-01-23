# compara-chuva
Comparativo de precipitação de qualquer modelo de input

## Descrição

Este projeto contém um notebook Jupyter para comparação de dados de precipitação (chuva) de duas fontes diferentes: **ONS** (Operador Nacional do Sistema Elétrico) e **TOK** (outra fonte de dados).

O notebook permite análise comparativa por pontos de interesse, gerando visualizações e estatísticas detalhadas das diferenças entre as fontes.

## Funcionalidades

- ✅ **Parâmetros Configuráveis**: Nome do modelo, horizonte de previsão e data da rodada
- ✅ **Input Dinâmico**: Caminho de entrada varia automaticamente conforme modelo e data
- ✅ **Análise Completa**: Estatísticas descritivas das diferenças entre fontes
- ✅ **Heatmaps**: Visualizações coloridas das diferenças por ponto e tempo
- ✅ **Acumulados**: Cálculo de diferenças positivas e negativas acumuladas
- ✅ **Desvio Padrão**: Análise de variabilidade das diferenças
- ✅ **Output Organizado**: Saídas estruturadas conforme o input

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/tok-yuri/compara-chuva.git
cd compara-chuva
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## Uso

### 1. Inicie o Jupyter Notebook

```bash
jupyter notebook
```

### 2. Abra o notebook

No navegador, abra o arquivo `compara_chuva.ipynb`

### 3. Configure os parâmetros

Na célula de configuração (Seção 1), ajuste os parâmetros conforme necessário:

```python
# Nome do modelo
nome_modelo = "MODELO_EXEMPLO"

# Horizonte de previsão (em dias ou horas)
horizonte = 7

# Data da rodada (formato: YYYYMMDD)
data_rodada = "20260123"

# Diretório base onde os dados estão armazenados
diretorio_base = "/dados"
```

### 4. Estrutura de diretórios esperada

O notebook espera a seguinte estrutura de diretórios:

```
/dados
└── {nome_modelo}
    └── {data_rodada}
        ├── ONS/
        │   └── dados_ons.csv (ou .xlsx, .parquet)
        └── TOK/
            └── dados_tok.csv (ou .xlsx, .parquet)
```

### 5. Formato dos dados

Os arquivos de dados devem conter no mínimo as seguintes colunas:
- **ponto** (ou local/estacao): Identificador do ponto de interesse
- **data** (ou date): Data/hora da medição
- **precipitacao_mm** (ou chuva/mm): Valor da precipitação em milímetros

Exemplo de formato CSV:

```csv
ponto,data,precipitacao_mm
Ponto_01,2026-01-01,15.5
Ponto_01,2026-01-02,22.3
Ponto_02,2026-01-01,18.7
...
```

### 6. Execute o notebook

Execute todas as células sequencialmente (`Cell > Run All`) ou célula por célula.

## Saídas

O notebook gera os seguintes arquivos no diretório de saída (`{input}/comparacao/`):

### Tabelas CSV
1. **estatisticas_por_ponto_{data}.csv**: Estatísticas completas por ponto
2. **acumulados_diferencas_{data}.csv**: Acumulados positivos e negativos
3. **desvio_padrao_diferencas_{data}.csv**: Desvio padrão por ponto
4. **matriz_diferencas_{data}.csv**: Matriz de diferenças (pontos x datas)

### Visualizações PNG
5. **heatmap_diferencas_{data}.png**: Heatmap das diferenças (ONS - TOK)
6. **heatmap_diferencas_absolutas_{data}.png**: Heatmap das diferenças absolutas
7. **graficos_acumulados_{data}.png**: Gráficos de barras dos acumulados
8. **distribuicao_diferencas_{data}.png**: Histograma e boxplot das diferenças

### Relatório
9. **relatorio_consolidado_{data}.txt**: Relatório textual com todas as estatísticas

## Exemplo de Uso

```python
# Configuração para modelo GFS rodado em 23/01/2026
nome_modelo = "GFS"
horizonte = 10
data_rodada = "20260123"
diretorio_base = "/dados/meteorologia"

# O notebook irá:
# - Ler dados de: /dados/meteorologia/GFS/20260123/ONS/
# - Ler dados de: /dados/meteorologia/GFS/20260123/TOK/
# - Salvar saídas em: /dados/meteorologia/GFS/20260123/comparacao/
```

## Interpretação dos Resultados

### Diferenças Positivas (ONS > TOK)
Indicam que a fonte ONS registrou valores **maiores** de precipitação que a fonte TOK.

### Diferenças Negativas (ONS < TOK)
Indicam que a fonte ONS registrou valores **menores** de precipitação que a fonte TOK.

### Desvio Padrão
Valores altos indicam maior **variabilidade** nas diferenças, sugerindo menor consistência entre as fontes.

### Heatmaps
- **Cores vermelhas**: ONS registrou mais chuva que TOK
- **Cores azuis**: TOK registrou mais chuva que ONS
- **Branco/neutro**: Valores similares entre as fontes

## Requisitos

- Python 3.8 ou superior
- Jupyter Notebook
- Pandas
- NumPy
- Matplotlib
- Seaborn
- openpyxl (para arquivos Excel)
- pyarrow (para arquivos Parquet)

## Modo de Demonstração

Se os arquivos de dados não forem encontrados, o notebook automaticamente gera dados de exemplo para demonstração das funcionalidades.

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests

## Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## Suporte

Para dúvidas ou problemas, abra uma issue no repositório do GitHub.
