# Automação de Processamento de Documentos (PDFS)

Este repositório apresenta uma solução autoral de **Processamento de Dados e Automação**, desenvolvida para otimizar o fluxo de documentos em larga escala. O projeto demonstra como transformar processos manuais de triagem em um pipeline digital eficiente, seguro e escalável.

> **Nota de Integridade:** Este projeto é uma demonstração. Todo o ambiente, dados e documentos são sintéticos, garantindo total isolamento de informações sensíveis e conformidade com boas práticas de privacidade.

---

###  Funcionalidades e Performance
O sistema foi projetado para resolver desafios reais de gestão documental, entregando:
*   **Processamento em Lote:** Leitura e extração automatizada de múltiplos arquivos PDF simultaneamente.
*   **Identificação Inteligente:** Reconhecimento de páginas e classificação baseada em padrões de texto.
*   **Segmentação Dinâmica:** Separação e organização de documentos por identificadores únicos, grupos e unidades.
*   **Consolidação de Saída:** Geração automática de relatórios gerenciais (Excel) e pacotes estruturados (ZIP) para distribuição.

---

###  Estrutura do Projeto
O fluxo de trabalho está dividido em dois núcleos principais:
*   `gerar_pdfs_demo.py`: Engine de simulação que cria a base de dados (PDFs sintéticos) para os testes.
*   `processar_documentos_demo.py`: O "cérebro" da automação, responsável pelo processamento, classificação e exportação final.

**Organização de Diretórios:**
*   `INPUT_PDFS/`: Repositório de entrada dos documentos brutos.
*   `OUTPUT_TMP/`: Área de processamento intermediário.
*   `OUTPUT_FINAL/`: Entrega final contendo o Relatório de Processamento (.xlsx) e o Pacote Estruturado (.zip).

---

###  Como Executar
Certifique-se de ter o Python instalado e execute os comandos abaixo no terminal:

```powershell
# 1. Gerar a base de documentos simulados
python gerar_pdfs_demo.py

# 2. Iniciar a automação do processamento
python processar_documentos_demo.py
