# 🚗 Porsche Sales Intelligence — Dashboard de Performance Comercial

> Projeto de análise de dados com pipeline de limpeza e padronização de uma base de vendas da Porsche, culminando em um dashboard executivo interativo.

🔗 **[Acesse o dashboard ao vivo](https://marylacryma.github.io/EstudoTesteDashboard/Projeto%20Dashboard%20Porsche/)**

---

## Sobre o projeto

Este projeto simula um cenário real de tratamento e visualização de dados comerciais. A base de partida continha 100 registros de vendas intencionalmente sujos — datas em múltiplos formatos, preços com separadores inconsistentes, quilometragem em km e milhas, nomes com capitalização incorreta, status com erros de digitação, entre outros problemas.

O objetivo foi criar um pipeline reproduzível de limpeza com regras documentadas (schema), transformar os dados em colunas padronizadas e construir um dashboard executivo para análise de performance comercial.

---

## Pipeline do projeto

```
Base bruta (.xlsx)
      │
      ▼
┌─────────────────────┐
│  Definição do       │
│  schema.md          │  Regras de validação e transformação por coluna
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  apply_schema.py    │  Geração das colunas _clean ao lado das originais
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Base limpa (.xlsx) │  100 linhas × 23 colunas (12 originais + 11 _clean)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Dashboard HTML     │  Visualização interativa publicada via GitHub Pages
└─────────────────────┘
```

---

## Schema de dados

O arquivo `schema.md` documenta as regras aplicadas a cada coluna. O princípio central é **não alterar os dados originais**: para cada coluna transformada, uma nova coluna `_clean` é criada ao lado.

| Coluna original | Coluna gerada | Transformação |
|---|---|---|
| `sale_date` | `sale_date_clean` | Normalização para ISO `AAAA-MM-DD`; datas inválidas → `"Inválido"` |
| `customer_name` | `customer_name_clean` | Title Case; hífen tratado como separador de nome composto |
| `porsche_model` | `porsche_model_clean` | Mapeamento para lista canônica de 40 modelos; desconhecidos em Title Case |
| `model_year` | `model_year_clean` | Conversão de extenso/abreviado para inteiro de 4 dígitos |
| `sale_price` | `sale_price_clean` | Normalização para número decimal USD (suporte a `k`, extenso, formato europeu) |
| `vehicle_mileage` | `vehicle_mileage_clean` | Conversão para número inteiro em milhas; KM convertido com fator 0.621371 |
| `payment_method` | `payment_method_clean` | Mapeamento para lista fixa de 9 métodos; variações e sinônimos unificados |
| `city` | `city_clean` | Title Case |
| `state` | `state_clean` | Sigla USPS 2 letras maiúsculas; nomes completos convertidos |
| `salesperson` | `salesperson_clean` | Title Case |
| `delivery_status` | `delivery_status_clean` | Mapeamento para lista fixa de 9 status; typos corrigidos automaticamente |

Problemas tratados na base original:

- Datas em 8+ formatos distintos (incluindo seriais do Excel e datas por extenso em inglês)
- Datas fisicamente impossíveis como `2024-02-30` e `April 31st`
- Preços com separadores ambíguos (ponto/vírgula), sufixo `k` e valores por extenso
- Quilometragem mista (milhas e km, com e sem unidade explícita)
- Nomes de estados por extenso e em minúsculas
- Status com pontuação excessiva (`delivered!!!`) e erros de digitação (`DELIVERD`)
- Anos de modelo escritos por extenso (`twenty twenty four`) e abreviados (`20-23`)

---

## Dashboard

O dashboard foi construído em HTML/CSS/JavaScript puro e publicado via GitHub Pages.

**KPIs principais**
- Receita total e ticket médio
- Volume de vendas e número de modelos distintos
- Modelo líder e cidade líder no período

**Visualizações**
- Ranking de modelos por cidade
- Distribuição de vendas por ano de modelo
- Evolução semestral dos modelos mais populares por cidade

**Filtros interativos**
- Modelo, ano do modelo, método de pagamento e cidade
- Filtros combinados com atualização dinâmica dos gráficos e KPIs
- Aba de insights executivos com resumo acionável dos dados filtrados

---

## Tecnologias utilizadas

- **Python** — pandas, openpyxl (limpeza e transformação dos dados)
- **HTML / CSS / JavaScript** — dashboard interativo
- **GitHub Pages** — publicação do dashboard
- **Excel** — base de dados e entrega da planilha tratada

---