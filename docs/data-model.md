# Modelo de Dados: Star Schema

## Contexto

Este projeto usa o dataset público da Olist (e-commerce brasileiro) para construir
um data lake analítico na AWS (S3 + Glue + Athena + QuickSight). O modelo de dados
segue a abordagem de Star Schema, otimizado para consultas analíticas (OLAP).

## Decisões de modelagem

### 1. Grão da tabela fato principal

**Decisão:** o grão de `fact_order_items` é **item de pedido** (uma linha por
produto dentro de um pedido), não "pedido inteiro".

**Raciocínio:** star schema é desenhado para OLAP, não OLTP, a regra de evitar
redundância (normalização) não se aplica aqui. Repetir `order_id` várias vezes
na fato é esperado e correto quando o grão é "item de pedido".

Regra prática adotada: **sempre escolher o grão mais fino que faça sentido para
o negócio**. Agregar depois é fácil (somar); desagregar depois é impossível
(o dado granular já não existe mais).

> Analogia: ao agregar dados por dia, ainda é possível derivar semanas e meses.
> Ao agregar direto por mês, não é mais possível recuperar a granularidade de
> dias ou semanas.

**Trade-off do grão "por pedido" (rejeitado):** perderíamos a capacidade de saber
o valor, quantidade e produto individual de cada item, só teríamos totais
agregados por pedido.

### 2. Reviews e Payments como fatos separadas (não dimensões)

**Decisão:** `fact_reviews` e `fact_payments` são tabelas fato próprias, não
dimensões, e se conectam ao restante do modelo apenas via `order_id` (fato-a-fato
via chave comum / conformação de fatos).

**Raciocínio:** verificação direta nas colunas dos CSVs mostrou que nenhuma das
duas tabelas tem FK direta para `product_id` ou `seller_id` apenas `order_id`.
Isso significa que, para conectar uma review ou um pagamento a um produto ou
vendedor específico, é necessário atravessar primeiro por `fact_order_items`.

Além disso, `order_payments` tem a coluna `payment_sequential`, indicando que um
mesmo pedido pode ter múltiplos registros de pagamento (pagamento dividido em
mais de uma forma) reforçando que é uma fato com grão próprio, não um atributo
simples de dimensão.

## Modelo final

```
fact_order_items (grão: item de pedido)
  - order_id, order_item_id, product_id (FK), seller_id (FK),
    customer_id (FK), purchase_date (FK), price, freight_value

fact_reviews (grão: review)
  - review_id, order_id, review_score, review_comment_message,
    review_creation_date

fact_payments (grão: parcela/forma de pagamento)
  - order_id, payment_sequential, payment_type,
    payment_installments, payment_value

dim_customers
dim_products
dim_sellers
dim_date
```