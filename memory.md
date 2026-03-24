# Memory — Decisões Estabelecidas pelo Usuário

> **Protocolo**: Sempre que o usuário estabelecer algo novo, a IA deve **primeiro atualizar este arquivo** e **depois** executar o plano.
> Este arquivo contém APENAS decisões do usuário, não informações técnicas do projeto.

---

## Fonte de Verdade
- O arquivo `X-Men_Reading_Order_final.xlsx` é a fonte de verdade para a reading order.
- Sempre que precisar recriar os JSONs, rodar `python generate_reading_order.py`.

## Estrutura dos Dados
- O JSON principal é `data/reading_order.json` (com todas as issues).
- Os JSONs por fase ficam em `data/phases/` (com ordem local dentro de cada fase).
- A coluna **"Main?"** do Excel → `Yes` = `essencial`, vazio = `recomendado`.

## Títulos com Volume
- O Excel usa volume nos títulos (ex: `X-Men vol. 5`), o que é **correto** para o usuário e para o JSON.
- O site readcomiconline usa formato por ano (ex: `x-men (2019)`), não por volume.
- A arquitetura de scraping deve tratar essa diferença internamente (strip vol. ao buscar no site).

## Slugs
- Não foram finalizados ainda — serão revisados em uma conversa futura.

## Limpeza do Projeto
- Não manter JSONs por ano (`reading_order_2019_2021.json`, etc.) — sempre usar por fase.
- Não manter backups antigos no repositório.
