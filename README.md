# Demonstracao de Processamento de Documentos

Esta e uma demonstracao independente de portfolio para processamento automatizado de PDFs.

O projeto esta totalmente isolado do ambiente de trabalho original:
- sem imports de outros arquivos do projeto real
- sem nomes de empresas
- sem referencias a instituicoes especificas
- apenas documentos sinteticos de demonstracao

## Arquivos

- `gerar_pdfs_demo.py`: cria os PDFs sinteticos de input
- `processar_documentos_demo.py`: processa os PDFs demo e gera as saidas organizadas

## Estrutura de pastas

- `INPUT_PDFS/`: documentos sinteticos de entrada
- `OUTPUT_TMP/PDFS_PROCESSADOS/`: PDFs processados
- `OUTPUT_FINAL/relatorio_processamento_documentos.xlsx`: relatorio final
- `OUTPUT_FINAL/pacote_documentos_processados.zip`: pacote ZIP com os documentos processados

## Como executar

```powershell
python gerar_pdfs_demo.py
python processar_documentos_demo.py
```

## O que este projeto demonstra

- leitura de PDFs em lote
- identificacao de paginas com base em texto
- separacao de documentos por identificador
- organizacao da saida por grupo e unidade
- geracao de relatorio e pacote ZIP final

## Seguro para mostrar publicamente

- codigo-fonte
- estrutura de pastas
- relatorio gerado
- PDFs sinteticos
- capturas de tela do fluxo
