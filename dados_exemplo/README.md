# Exemplo de Dados de Entrada

Este diretório contém exemplos de estrutura e formato de dados para o notebook de comparação.

## Estrutura de Diretórios

```
dados_exemplo/
└── MODELO_EXEMPLO/
    └── 20260123/
        ├── ONS/
        │   └── precipitacao_ons.csv
        └── TOK/
            └── precipitacao_tok.csv
```

## Formato dos Arquivos

### Opção 1: CSV (recomendado)
```csv
ponto,data,precipitacao_mm
Ponto_01,2026-01-01,15.5
Ponto_01,2026-01-02,22.3
```

### Opção 2: Excel (.xlsx)
Mesma estrutura em planilha Excel

### Opção 3: Parquet
Formato binário otimizado para grandes volumes de dados

## Colunas Obrigatórias

1. **ponto** (ou local, estacao): Identificador do ponto de medição
2. **data** (ou date, datetime): Data/hora da medição
3. **precipitacao_mm** (ou chuva, mm, precip): Valor em milímetros

## Notas

- As colunas podem ter nomes diferentes; o notebook tenta identificá-las automaticamente
- Datas devem estar em formato reconhecível pelo pandas (ISO 8601 recomendado)
- Valores ausentes serão tratados como 0 mm
