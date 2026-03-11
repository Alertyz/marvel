#!/usr/bin/env python3
"""
Entry point for the scraping/downloading tools.

Usage:
    python run_scrapper.py <command> [options]

Commands:
    scrape          Fase 1: coletar URLs com browsers paralelos
    download        Fase 2: baixar imagens das URLs salvas
    run             Scrape + Download em sequencia
    validate        Verificar integridade dos downloads
    validate --fix  Corrigir problemas encontrados
    flags           Mostrar flags de validacao
    status          Mostrar progresso geral
    status --detail Status detalhado por issue
    list-phases     Listar fases disponiveis
    list-series     Listar series disponiveis
    rescrape        Resetar issues para re-scrape

Filtros (funcionam com scrape/download/run/status):
    --series "X-Men"        Filtrar por serie
    --phase "Fall of X"     Filtrar por fase
    --from-bookmark         Apenas apos o bookmark
    --order 10-50           Range de ordem especifico
"""

from scrapping.cli import main

if __name__ == "__main__":
    main()
