# Schema de Padronização — Vendas Porsche

## Princípio geral
- As colunas originais **nunca são alteradas ou removidas**.
- Para cada coluna que exigir transformação, criar uma **nova coluna** ao lado da original, com o sufixo `_clean`.
  - Exemplo: `sale_date` (original) → `sale_date_clean` (nova, ao lado).
- Quando um valor não puder ser interpretado com segurança, a coluna `_clean` recebe o texto fixo `"Inválido"`.
- Colunas sem necessidade de transformação (ex.: `sale_id`) não recebem coluna `_clean`.

---

## 1. `sale_id`
- Sem transformação. Manter como está.

---

## 2. `sale_date` → `sale_date_clean`
**Formato de saída:** ISO `AAAA-MM-DD`

**Formatos de entrada esperados (variações encontradas na base):**
- Datas numéricas com separadores variados: `MM/DD/AAAA`, `AAAA-MM-DD`, `AAAA.MM.DD`, `AAAA/DD/MM`, `MM-DD-AA`, `DD/MM/AAAA`
- Números seriais do Excel (ex: `45400`, `45434`) → converter a partir da data-base do Excel (1900-01-00 / sistema de serial date)
- Datas escritas por extenso em inglês (ex: `September 17, 2024`, `Dec 25th 2024`, `Jun 18th 2027`)
- Datas com dia fora do intervalo do mês (ex: `2024-02-30`, dia 31 em mês de 30 dias, `2024-10-40`) → **inválidas**
- Datas com mês fora do intervalo 1–12 (quando a ambiguidade DD/MM não resolve) → **inválidas**

**Regras:**
1. Tentar interpretar a data em todos os formatos conhecidos acima.
2. Validar que o resultado é uma data civil real (dia existe no mês, mês entre 1 e 12, ano plausível).
3. Se a data for inválida (dia/mês inexistente, ambiguidade não resolvida, formato não reconhecido) → `sale_date_clean = "Inválido"`.
4. Se válida → gravar como texto/data no formato `AAAA-MM-DD`.

---

## 3. `customer_name` → `customer_name_clean`
**Formato de saída:** Title Case (primeira letra de cada parte do nome em maiúscula)

**Regras:**
1. Normalizar capitalização: `SOPHIA Miller` → `Sophia Miller`.
2. Hífen no nome é tratado como **separador de nome composto** (não é erro): `Daniel-Jones` → `Daniel Jones`; `Ryan-Cooper` → `Ryan Cooper`; `Tyler-Morris` → `Tyler Morris`.
3. Remover espaços duplicados/excedentes nas bordas.

---

## 4. `porsche_model` → `porsche_model_clean`
**Formato de saída:** Title Case canônico, conforme lista de modelos válidos

**Lista canônica de modelos válidos:**
- `911 Carrera`
- `911 Carrera S`
- `911 Carrera GTS`
- `911 Turbo`
- `911 Turbo S`
- `911 GT3`
- `911 GT3 RS`
- `911 Dakar`
- `911 Targa 4`
- `911 Targa 4S`
- `718 Cayman`
- `718 Cayman S`
- `718 Cayman GT4 RS`
- `718 Boxster`
- `718 Boxster GTS`
- `718 Spyder RS`
- `Cayenne`
- `Cayenne S`
- `Cayenne Coupe`
- `Cayenne E-Hybrid`
- `Cayenne Turbo`
- `Cayenne Turbo GT`
- `Macan`
- `Macan S`
- `Macan T`
- `Macan GTS`
- `Macan Electric`
- `Panamera`
- `Panamera 4`
- `Panamera 4S`
- `Panamera Turbo`
- `Panamera Turbo S`
- `Panamera 4 E-Hybrid`
- `Taycan`
- `Taycan 4S`
- `Taycan GTS`
- `Taycan Turbo`
- `Taycan Turbo S`
- `Taycan Cross Turismo`

**Regras:**
1. Normalizar capitalização e espaçamento, depois comparar com a lista canônica acima (comparação insensível a maiúsculas/minúsculas e a espaços extras).
2. Preservar caracteres válidos de aparar/pontuação que fazem parte do nome do modelo: números (`718`, `911`, `4`, `4S`), hífen em `E-Hybrid`, e siglas (`S`, `T`, `GTS`, `GT3`, `GT3 RS`, `RS`, `Turbo S`).
3. Se o valor corresponder a um modelo da lista canônica (mesmo com capitalização/espaçamento diferentes) → gravar exatamente como está na lista canônica.
4. Se o valor **não corresponder a nenhum modelo da lista canônica** (modelo desconhecido/não cadastrado) → **não marcar como "Inválido"**; em vez disso, aplicar Title Case (primeira letra de cada palavra em maiúscula) e gravar o resultado.

---

## 5. `model_year` → `model_year_clean`
**Formato de saída:** número inteiro de 4 dígitos (ex.: `2024`)

**Formatos de entrada esperados:**
- Numérico direto: `2022`, `2024`
- Por extenso em inglês: `twenty twenty four`, `two thousand twenty one`
- Abreviado com hífen ou espaço: `20-23`, `20 24`, `20-21`

**Regras:**
1. Tentar converter para número de 4 dígitos quando o padrão for reconhecível com segurança (extenso completo, ou abreviação numérica tipo `20-23` → `2023`).
2. Validar que o ano resultante é plausível (entre 2015 e o ano atual + 1, ajustável conforme a base).
3. Se não for possível interpretar com segurança (ambíguo, incompleto, fora de faixa plausível) → `"Inválido"`.

---

## 6. `sale_price` → `sale_price_clean`
**Formato de saída:** número decimal puro em USD, sem símbolos (ex.: `79500.00`)

**Formatos de entrada esperados:**
- `$79,500.00`, `$132000`, `$96.300` (separador de milhar com ponto)
- `235000 USD`, `USD 112.750`, `USD $96,300`
- `89.750,00` (formato europeu: ponto = milhar, vírgula = decimal)
- Abreviações: `$121k`, `$139k`, `188k USD`
- Por extenso: `eighty two thousand USD`, `two hundred thousand USD`

**Regras:**
1. Remover símbolos de moeda (`$`, `USD`, `dollars`) e identificar o separador decimal correto pelo contexto (último separador antes de 2 dígitos finais = decimal).
2. Expandir abreviações `k` → multiplicar por 1.000 (ex.: `$121k` → `121000`).
3. Interpretar valores por extenso em inglês para número.
4. Resultado final sempre como número puro, 2 casas decimais, sem separador de milhar, assumindo USD.
5. Se não for possível interpretar com segurança → `"Inválido"`.

---

## 7. `vehicle_mileage` → `vehicle_mileage_clean`
**Formato de saída:** número inteiro de milhas (ex.: `9800`)

**Formatos de entrada esperados:**
- `9,800 miles`, `41,000mi`, `1.200 mi` (ponto como separador de milhar)
- `Miles: 6,400`, `Miles 8.900`, `KM 18,900`
- `zero miles`, `new`, `new car`, `0 miles`
- Números por extenso: `twelve thousand miles`, `fifteen thousand miles`
- Número solto sem unidade: `28`, `9.5`

**Regras:**
1. `new`, `new car`, `zero miles`, `zero` → `0`.
2. Valores explicitamente em **KM** (`KM 18,900`, `Miles` nunca aparece) → converter para milhas (`milhas = km * 0.621371`), arredondar para inteiro.
3. Valores explicitamente em milhas (`mi`, `miles`) → manter, apenas limpar formatação e converter por extenso quando aplicável.
4. Número solto **sem unidade explícita** (ex.: `28`, `9.5`) → assumir milhas, conforme decisão do usuário.
5. Resultado sempre como número inteiro de milhas.
6. Se não for possível interpretar com segurança → `"Inválido"`.

---

## 8. `payment_method` → `payment_method_clean`
**Formato de saída:** valor padronizado a partir da lista fixa abaixo

**Lista fixa de valores válidos:**
- `Credit Card`
- `Debit Card`
- `Cash`
- `Bank Transfer`
- `Wire Transfer`
- `Financing`
- `Lease`
- `ACH`
- `Crypto`

**Mapeamento de variações (sinônimos → valor padrão):**
| Variações encontradas | Valor padronizado |
|---|---|
| `Credit card`, `CreditCard`, `credit`, `credit card payment`, `CASH payment` (cash) | `Credit Card` / `Cash` (conforme o termo-base) |
| `debit card` | `Debit Card` |
| `cash`, `CASH`, `cash payment` | `Cash` |
| `bank transfer`, `Bank Transfer`, `bank-transfer`, `bank_transfer`, `bank wire`, `Bank wire`, `Bank Wire` | `Bank Transfer` |
| `wire`, `wire transfer`, `WireTransfer`, `wire-transfer`, `Wire Transfer` | `Wire Transfer` |
| `Financing`, `Financing plan`, `Financing Plan`, `finance` | `Financing` |
| `lease`, `Leasing`, `lease plan` | `Lease` |
| `ACH payment`, `ACH` | `ACH` |
| `crypto`, `Crypto`, `crypto payment` | `Crypto` |

**Regras:**
1. Remover variações de capitalização, pontuação, hífen/underscore.
2. Mapear para o valor mais próximo da lista fixa.
3. Se não houver correspondência clara → `"Inválido"`.

---

## 9. `city` → `city_clean`
**Formato de saída:** Title Case

**Regras:**
1. Padronizar capitalização (ex.: `boston` → `Boston`; `new york` → `New York`).
2. Manter nomes compostos e abreviações próprias da cidade (ex.: `St. Louis`).

---

## 10. `state` → `state_clean`
**Formato de saída:** sigla de 2 letras maiúsculas (padrão USPS)

**Regras:**
1. Se já estiver em sigla (`ma`, `TX`) → padronizar para maiúscula (`MA`, `TX`).
2. Se estiver por extenso (`Washington`, `colorado`, `Massachusetts`) → converter para a sigla correspondente.
3. Se não for possível identificar o estado → `"Inválido"`.

---

## 11. `salesperson` → `salesperson_clean`
**Formato de saída:** Title Case

**Regras:**
1. Padronizar capitalização (ex.: `AMANDA scott` → `Amanda Scott`; `kevin` → `Kevin`).
2. Mesmo tratamento de hífen do `customer_name`, se aplicável.

---

## 12. `delivery_status` → `delivery_status_clean`
**Formato de saída:** valor padronizado a partir da lista fixa abaixo

**Lista fixa de valores válidos:**
- `Delivered`
- `Pending`
- `Pending Approval`
- `In Transit`
- `Shipped`
- `Cancelled`
- `Awaiting Delivery`
- `Awaiting Pickup`
- `Awaiting Review` / `Pending Review`

**Regras:**
1. Remover pontuação extra (`!!!`, `.`, `!!`).
2. Corrigir erros de digitação evidentes (ex.: `DELIVERD` → `Delivered`).
3. Padronizar capitalização e mapear variações equivalentes para a lista fixa (ex.: `awaiting delivery` = `Awaiting Delivery`; `in-transit` = `In Transit`).
4. Se não houver correspondência clara com a lista fixa → `"Inválido"`.

---

## Resumo das colunas geradas

| Coluna original | Nova coluna | Tipo de saída |
|---|---|---|
| sale_id | — | (sem alteração) |
| sale_date | sale_date_clean | Data ISO `AAAA-MM-DD` ou `"Inválido"` |
| customer_name | customer_name_clean | Texto (Title Case) |
| porsche_model | porsche_model_clean | Texto (Title Case canônico; modelos desconhecidos em Title Case simples, nunca "Inválido") |
| model_year | model_year_clean | Número inteiro (4 dígitos) ou `"Inválido"` |
| sale_price | sale_price_clean | Número decimal (USD) ou `"Inválido"` |
| vehicle_mileage | vehicle_mileage_clean | Número inteiro (milhas) ou `"Inválido"` |
| payment_method | payment_method_clean | Texto padronizado (lista fixa) ou `"Inválido"` |
| city | city_clean | Texto (Title Case) |
| state | state_clean | Sigla 2 letras (maiúscula) ou `"Inválido"` |
| salesperson | salesperson_clean | Texto (Title Case) |
| delivery_status | delivery_status_clean | Texto padronizado (lista fixa) ou `"Inválido"` |
