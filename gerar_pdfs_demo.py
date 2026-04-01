from pathlib import Path
import shutil

import fitz


PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_INPUT_PDFS = PASTA_PROJETO / "INPUT_PDFS"

LARGURA_PAGINA = 595
ALTURA_PAGINA = 842

DOCUMENTOS_DEMO = [
    {
        "nome_arquivo": "GRUPO_A U01.pdf",
        "nome_entidade": "ENTIDADE ALFA",
        "codigo_documento": "DOC-A-001",
        "regioes_cobertura": "Regiao 01; Regiao 02; Regiao 03",
        "codigo_validacao": "AUT-A-2026-0001",
        "codigo_registro": "REG-1001",
        "veiculos": [
            ["ABC1D23", "DEF4G56", "GHI7J89", "JKL0M12"],
            ["NOP3Q45", "RST6U78", "VWX9Y01", "ZAB2C34"],
            ["EFG5H67", "IJK8L90", "MNO1P23", "QRS4T56"],
        ],
        "separar_pagina_validacao": True,
    },
    {
        "nome_arquivo": "GRUPO_B U02.pdf",
        "nome_entidade": "ENTIDADE BETA",
        "codigo_documento": "DOC-B-002",
        "regioes_cobertura": "Regiao 04; Regiao 05; Regiao 06",
        "codigo_validacao": "AUT-B-2026-0002",
        "codigo_registro": "REG-1002",
        "veiculos": [
            ["LMN1A23", "PQR4B56", "STU7C89", "VWX0D12"],
            ["YZA3E45", "BCD6F78", "EFG9G01", "HIJ2H34"],
            ["KLM5I67", "NOP8J90", "QRS1K23", "TUV4L56"],
        ],
        "separar_pagina_validacao": False,
    },
    {
        "nome_arquivo": "GRUPO_C U03.pdf",
        "nome_entidade": "ENTIDADE GAMA",
        "codigo_documento": "DOC-C-003",
        "regioes_cobertura": "Regiao 07; Regiao 08; Regiao 09",
        "codigo_validacao": "AUT-C-2026-0003",
        "codigo_registro": "REG-1003",
        "veiculos": [
            ["QWE1R23", "TYU4I56", "OPA7S89", "DFG0H12"],
            ["JKL3Z45", "XCV6B78", "NMQ9W01", "ERT2Y34"],
            ["UIO5P67", "ASD8F90", "GHJ1K23", "LZX4C56"],
        ],
        "separar_pagina_validacao": False,
    },
]


def montar_linhas_veiculos(veiculos, codigo_registro):
    linhas = []

    for indice, placa in enumerate(veiculos):
        categoria = "Principal" if indice % 2 == 0 else "Apoio"
        linhas.append(f"{placa}  {codigo_registro}  {categoria}")

    return linhas


def texto_primeira_pagina(documento, numero_pagina, total_paginas):
    linhas = [
        "Demonstracao de Processamento de Documentos",
        "",
        "Visao Geral da Entidade",
        f"Entidade: {documento['nome_entidade']}",
        f"Documento: {documento['codigo_documento']}",
        "Emitido em: 2026-03-31",
        "Valido ate: 2026-06-30",
        "",
        "Cadastro de Veiculos",
        "Placa  Registro  Categoria",
        *montar_linhas_veiculos(documento["veiculos"][0], documento["codigo_registro"]),
        "",
        f"Pagina {numero_pagina}/{total_paginas}",
    ]
    return "\n".join(linhas)


def texto_pagina_cadastro(documento, veiculos, numero_pagina, total_paginas):
    linhas = [
        "Demonstracao de Processamento de Documentos",
        "Continuacao do Cadastro de Veiculos",
        "",
        "Placa  Registro  Categoria",
        *montar_linhas_veiculos(veiculos, documento["codigo_registro"]),
        "",
        f"Pagina {numero_pagina}/{total_paginas}",
    ]
    return "\n".join(linhas)


def texto_pagina_resumo(documento, veiculos, numero_pagina, total_paginas):
    linhas = [
        "Demonstracao de Processamento de Documentos",
        "Resumo do Cadastro de Veiculos",
        "",
        *montar_linhas_veiculos(veiculos, documento["codigo_registro"]),
        "",
        "Classes de Risco",
        "Classe A: Materiais inflamaveis",
        "Classe B: Materiais corrosivos",
        "Classe C: Materiais pressurizados",
        f"Regioes de Cobertura: {documento['regioes_cobertura']}",
        "",
        f"Pagina {numero_pagina}/{total_paginas}",
    ]
    return "\n".join(linhas)


def texto_pagina_validacao(documento, numero_pagina, total_paginas):
    linhas = [
        "Demonstracao de Processamento de Documentos",
        "",
        "Validacao do Documento",
        "A autenticidade deste arquivo pode ser verificada no ambiente de demonstracao.",
        f"Codigo de validacao: {documento['codigo_validacao']}",
        "",
        f"Pagina {numero_pagina}/{total_paginas}",
    ]
    return "\n".join(linhas)


def escrever_texto(pagina, texto):
    area_texto = fitz.Rect(40, 40, LARGURA_PAGINA - 40, ALTURA_PAGINA - 40)
    pagina.insert_textbox(
        area_texto,
        texto,
        fontsize=11,
        fontname="helv",
        lineheight=1.25,
        align=0,
    )


def montar_pdf_demo(documento):
    PASTA_INPUT_PDFS.mkdir(parents=True, exist_ok=True)
    caminho_saida = PASTA_INPUT_PDFS / documento["nome_arquivo"]
    total_paginas = 5 if documento["separar_pagina_validacao"] else 4
    pdf = fitz.open()

    try:
        pagina_1 = pdf.new_page(width=LARGURA_PAGINA, height=ALTURA_PAGINA)
        escrever_texto(pagina_1, texto_primeira_pagina(documento, 1, total_paginas))

        pagina_2 = pdf.new_page(width=LARGURA_PAGINA, height=ALTURA_PAGINA)
        escrever_texto(
            pagina_2,
            texto_pagina_cadastro(documento, documento["veiculos"][1], 2, total_paginas),
        )

        pagina_3 = pdf.new_page(width=LARGURA_PAGINA, height=ALTURA_PAGINA)
        escrever_texto(
            pagina_3,
            texto_pagina_cadastro(documento, documento["veiculos"][2], 3, total_paginas),
        )

        pagina_4 = pdf.new_page(width=LARGURA_PAGINA, height=ALTURA_PAGINA)
        texto_pagina_4 = texto_pagina_resumo(
            documento,
            documento["veiculos"][2][-2:],
            4,
            total_paginas,
        )
        if not documento["separar_pagina_validacao"]:
            texto_pagina_4 += (
                f"\n\nValidacao do Documento\n"
                f"Codigo de validacao: {documento['codigo_validacao']}"
            )
        escrever_texto(pagina_4, texto_pagina_4)

        if documento["separar_pagina_validacao"]:
            pagina_5 = pdf.new_page(width=LARGURA_PAGINA, height=ALTURA_PAGINA)
            escrever_texto(pagina_5, texto_pagina_validacao(documento, 5, total_paginas))

        if caminho_saida.exists():
            caminho_saida.unlink()

        pdf.save(str(caminho_saida))
    finally:
        pdf.close()


def gerar_arquivos_demo():
    if PASTA_INPUT_PDFS.exists():
        shutil.rmtree(PASTA_INPUT_PDFS)

    for documento in DOCUMENTOS_DEMO:
        montar_pdf_demo(documento)

    return PASTA_INPUT_PDFS


if __name__ == "__main__":
    pasta = gerar_arquivos_demo()
    print("PDFs de demonstracao criados em:", pasta)
