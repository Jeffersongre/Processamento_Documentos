import re
import shutil
import time
from pathlib import Path

import fitz
import pandas as pd
from tqdm import tqdm


PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_INPUT_PDFS = PASTA_PROJETO / "INPUT_PDFS"
PASTA_OUTPUT_TMP = PASTA_PROJETO / "OUTPUT_TMP"
PASTA_PDFS_PROCESSADOS = PASTA_OUTPUT_TMP / "PDFS_PROCESSADOS"
PASTA_OUTPUT_FINAL = PASTA_PROJETO / "OUTPUT_FINAL"

MODO_TESTE = False
LIMITE_PDFS_TESTE = 2
PLACA_TESTE = "ABC1D23"

SALVAR_CHECKPOINT_A_CADA = 0
CRIAR_ZIP_FINAL = True
JANELA_BUSCA_PAGINAS_FINAIS = 3

PADRAO_PLACA = re.compile(
    r"\b(?:[A-Z]{3}[0-9]{4}|[A-Z]{3}[0-9][A-Z][0-9]{2})\b"
)

COLUNAS_RELATORIO = [
    "PDF_ORIGEM",
    "GRUPO",
    "UNIDADE",
    "ENTIDADE",
    "DOCUMENTO",
    "PLACA",
    "TOTAL_PAGINAS_ORIGEM",
    "PRIMEIRA_PAGINA",
    "PAGINA_PLACA",
    "PAGINA_RESUMO",
    "PAGINA_VALIDACAO",
    "PAGINAS_FINAIS",
    "PAGINAS_SAIDA",
    "ARQUIVO_SAIDA",
    "STATUS",
]


def preparar_pastas_saida():
    PASTA_OUTPUT_TMP.mkdir(parents=True, exist_ok=True)
    PASTA_PDFS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    PASTA_OUTPUT_FINAL.mkdir(parents=True, exist_ok=True)


def limpar_arquivos_anteriores():
    for caminho in [
        PASTA_OUTPUT_FINAL / "document_processing_report.xlsx",
        PASTA_OUTPUT_FINAL / "processed_documents_bundle.zip",
        PASTA_OUTPUT_FINAL / "relatorio_processamento_documentos.xlsx",
        PASTA_OUTPUT_FINAL / "pacote_documentos_processados.zip",
    ]:
        if caminho.exists() and caminho.is_file():
            caminho.unlink()

    if PASTA_PDFS_PROCESSADOS.exists():
        shutil.rmtree(PASTA_PDFS_PROCESSADOS)

    for item in PASTA_OUTPUT_TMP.iterdir():
        if item.is_dir():
            shutil.rmtree(item)

    PASTA_PDFS_PROCESSADOS.mkdir(parents=True, exist_ok=True)


def normalizar_texto(texto):
    if texto is None:
        return ""
    return str(texto).strip().upper()


def normalizar_nome_arquivo(texto):
    texto = normalizar_texto(texto)
    texto = re.sub(r'[\\/:*?"<>|]+', "_", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def ler_texto_pagina(documento, indice_pagina):
    return normalizar_texto(documento[indice_pagina].get_text("text"))


def tem_conteudo_resumo(texto):
    return "CLASSES DE RISCO" in texto or "REGIOES DE COBERTURA" in texto


def tem_conteudo_validacao(texto):
    return "VALIDACAO DO DOCUMENTO" in texto or "CODIGO DE VALIDACAO" in texto


def encontrar_paginas_finais(textos_paginas, janela=3):
    total_paginas = len(textos_paginas)
    inicio = max(0, total_paginas - janela)
    paginas_finais = []

    for indice in range(inicio, total_paginas):
        texto = textos_paginas[indice]
        eh_resumo = tem_conteudo_resumo(texto)
        eh_validacao = tem_conteudo_validacao(texto)

        if eh_resumo or eh_validacao:
            paginas_finais.append(
                {
                    "indice": indice,
                    "eh_resumo": eh_resumo,
                    "eh_validacao": eh_validacao,
                }
            )

    if paginas_finais:
        return paginas_finais

    for indice, texto in enumerate(textos_paginas):
        eh_resumo = tem_conteudo_resumo(texto)
        eh_validacao = tem_conteudo_validacao(texto)

        if eh_resumo or eh_validacao:
            paginas_finais.append(
                {
                    "indice": indice,
                    "eh_resumo": eh_resumo,
                    "eh_validacao": eh_validacao,
                }
            )

    return paginas_finais


def extrair_paginas_placas(textos_paginas):
    linhas = []

    for indice_pagina, texto in enumerate(textos_paginas):
        for placa in PADRAO_PLACA.findall(texto):
            linhas.append({"PLACA": placa, "PAGINA_PLACA": indice_pagina})

    if not linhas:
        return pd.DataFrame(columns=["PLACA", "PAGINA_PLACA"])

    df_placas = pd.DataFrame(linhas)
    return (
        df_placas.sort_values(["PLACA", "PAGINA_PLACA"])
        .drop_duplicates(subset=["PLACA"], keep="first")
        .reset_index(drop=True)
    )


def extrair_metadados_documento(texto_primeira_pagina):
    linhas = [linha.strip() for linha in texto_primeira_pagina.splitlines() if linha.strip()]
    nome_entidade = None
    codigo_documento = None

    for linha in linhas:
        if linha.startswith("Entidade:"):
            nome_entidade = linha.split(":", 1)[1].strip()
        elif linha.startswith("Documento:"):
            codigo_documento = linha.split(":", 1)[1].strip()

    return {
        "nome_entidade": nome_entidade,
        "codigo_documento": codigo_documento,
    }


def obter_grupo_por_nome_arquivo(nome_arquivo):
    partes = normalizar_nome_arquivo(Path(str(nome_arquivo)).stem).split()
    return partes[0] if partes else "GRUPO"


def obter_unidade_por_nome_arquivo(nome_arquivo):
    partes = normalizar_nome_arquivo(Path(str(nome_arquivo)).stem).split()
    return partes[-1] if partes else "UNIDADE"


def executar_com_tentativas(funcao, tentativas=3, espera_segundos=2):
    ultimo_erro = None

    for tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        except Exception as erro:
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(espera_segundos)

    raise ultimo_erro


def paginas_para_texto(indices_paginas):
    paginas = [indice + 1 for indice in indices_paginas if indice is not None]
    if not paginas:
        return None
    return ", ".join(str(pagina) for pagina in paginas)


def montar_paginas_saida(primeira_pagina, pagina_placa, informacoes_paginas_finais):
    paginas = [primeira_pagina, pagina_placa]
    paginas.extend(item["indice"] for item in informacoes_paginas_finais)

    paginas_unicas = []
    for pagina in paginas:
        if pagina is None or pagina in paginas_unicas:
            continue
        paginas_unicas.append(pagina)

    return paginas_unicas


def montar_status(pagina_placa, informacoes_paginas_finais):
    if pagina_placa is None:
        return "PLACA NAO ENCONTRADA"

    encontrou_resumo = any(item["eh_resumo"] for item in informacoes_paginas_finais)
    encontrou_validacao = any(item["eh_validacao"] for item in informacoes_paginas_finais)

    if not encontrou_resumo and not encontrou_validacao:
        return "PAGINAS DE RESUMO E VALIDACAO NAO ENCONTRADAS"
    if not encontrou_resumo:
        return "PAGINA DE RESUMO NAO ENCONTRADA"
    if not encontrou_validacao:
        return "PAGINA DE VALIDACAO NAO ENCONTRADA"

    return "OK"


def montar_pdf_saida(documento_origem, paginas_origem, caminho_saida):
    if not paginas_origem:
        raise ValueError("Nenhuma pagina selecionada para a saida.")

    novo_pdf = fitz.open()

    try:
        largura = 842
        altura = 595
        areas = [
            fitz.Rect(0, 0, largura / 2, altura),
            fitz.Rect(largura / 2, 0, largura, altura),
        ]

        for inicio in range(0, len(paginas_origem), 2):
            pagina_nova = novo_pdf.new_page(width=largura, height=altura)
            bloco_paginas = paginas_origem[inicio:inicio + 2]

            for area, pagina_origem in zip(areas, bloco_paginas):
                pagina_nova.show_pdf_page(area, documento_origem, pagina_origem)

        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        if caminho_saida.exists():
            caminho_saida.unlink()

        novo_pdf.save(str(caminho_saida))
    finally:
        novo_pdf.close()


def listar_pdfs_disponiveis():
    if not PASTA_INPUT_PDFS.exists():
        raise FileNotFoundError(f"Pasta de input nao encontrada: {PASTA_INPUT_PDFS}")

    arquivos = sorted(PASTA_INPUT_PDFS.glob("*.pdf"))
    if MODO_TESTE:
        arquivos = arquivos[:LIMITE_PDFS_TESTE]
    return arquivos


def filtrar_placas(df_placas):
    if not MODO_TESTE or not PLACA_TESTE:
        return df_placas
    return df_placas[df_placas["PLACA"] == normalizar_texto(PLACA_TESTE)].copy()


def montar_registro(
    pdf_origem,
    grupo,
    unidade,
    entidade,
    documento,
    placa,
    total_paginas_origem,
    primeira_pagina,
    pagina_placa,
    pagina_resumo,
    pagina_validacao,
    paginas_finais,
    paginas_saida,
    arquivo_saida,
    status,
):
    return {
        "PDF_ORIGEM": pdf_origem,
        "GRUPO": grupo,
        "UNIDADE": unidade,
        "ENTIDADE": entidade,
        "DOCUMENTO": documento,
        "PLACA": placa,
        "TOTAL_PAGINAS_ORIGEM": total_paginas_origem,
        "PRIMEIRA_PAGINA": primeira_pagina + 1 if primeira_pagina is not None else None,
        "PAGINA_PLACA": pagina_placa + 1 if pagina_placa is not None else None,
        "PAGINA_RESUMO": pagina_resumo + 1 if pagina_resumo is not None else None,
        "PAGINA_VALIDACAO": pagina_validacao + 1 if pagina_validacao is not None else None,
        "PAGINAS_FINAIS": paginas_para_texto(paginas_finais),
        "PAGINAS_SAIDA": paginas_para_texto(paginas_saida),
        "ARQUIVO_SAIDA": str(arquivo_saida) if arquivo_saida else None,
        "STATUS": status,
    }


def processar_documento_pdf(caminho_pdf):
    resultados = []
    pdf_origem = caminho_pdf.name
    grupo = obter_grupo_por_nome_arquivo(pdf_origem)
    unidade = obter_unidade_por_nome_arquivo(pdf_origem)

    documento_origem = fitz.open(str(caminho_pdf))

    try:
        total_paginas = len(documento_origem)
        if total_paginas == 0:
            resultados.append(
                montar_registro(
                    pdf_origem=pdf_origem,
                    grupo=grupo,
                    unidade=unidade,
                    entidade=None,
                    documento=None,
                    placa=None,
                    total_paginas_origem=0,
                    primeira_pagina=None,
                    pagina_placa=None,
                    pagina_resumo=None,
                    pagina_validacao=None,
                    paginas_finais=[],
                    paginas_saida=[],
                    arquivo_saida=None,
                    status="PDF VAZIO",
                )
            )
            return resultados

        metadados = extrair_metadados_documento(documento_origem[0].get_text("text"))
        pasta_saida = PASTA_PDFS_PROCESSADOS / grupo / unidade
        pasta_saida.mkdir(parents=True, exist_ok=True)

        textos_paginas = [
            ler_texto_pagina(documento_origem, indice_pagina)
            for indice_pagina in range(total_paginas)
        ]
        primeira_pagina = 0
        informacoes_paginas_finais = encontrar_paginas_finais(
            textos_paginas,
            janela=JANELA_BUSCA_PAGINAS_FINAIS,
        )
        paginas_finais = [item["indice"] for item in informacoes_paginas_finais]
        pagina_resumo = next(
            (item["indice"] for item in informacoes_paginas_finais if item["eh_resumo"]),
            None,
        )
        pagina_validacao = next(
            (
                item["indice"]
                for item in reversed(informacoes_paginas_finais)
                if item["eh_validacao"]
            ),
            None,
        )

        df_placas = extrair_paginas_placas(textos_paginas)
        df_placas = filtrar_placas(df_placas)

        print(
            f"\nPDF: {pdf_origem} | Grupo: {grupo} | Unidade: {unidade} | "
            f"Placas encontradas: {len(df_placas)} | "
            f"Paginas finais: {paginas_para_texto(paginas_finais) or '-'}"
        )

        if df_placas.empty:
            resultados.append(
                montar_registro(
                    pdf_origem=pdf_origem,
                    grupo=grupo,
                    unidade=unidade,
                    entidade=metadados["nome_entidade"],
                    documento=metadados["codigo_documento"],
                    placa=None,
                    total_paginas_origem=total_paginas,
                    primeira_pagina=primeira_pagina,
                    pagina_placa=None,
                    pagina_resumo=pagina_resumo,
                    pagina_validacao=pagina_validacao,
                    paginas_finais=paginas_finais,
                    paginas_saida=[primeira_pagina, *paginas_finais],
                    arquivo_saida=None,
                    status="NENHUMA PLACA ENCONTRADA",
                )
            )
            return resultados

        for _, linha in df_placas.iterrows():
            placa = normalizar_nome_arquivo(linha["PLACA"])
            pagina_placa = int(linha["PAGINA_PLACA"])
            paginas_saida = montar_paginas_saida(
                primeira_pagina,
                pagina_placa,
                informacoes_paginas_finais,
            )
            arquivo_saida = pasta_saida / f"{placa}.pdf"

            try:
                executar_com_tentativas(
                    lambda paginas=paginas_saida, caminho=arquivo_saida: montar_pdf_saida(
                        documento_origem,
                        paginas,
                        caminho,
                    )
                )

                resultados.append(
                    montar_registro(
                        pdf_origem=pdf_origem,
                        grupo=grupo,
                        unidade=unidade,
                        entidade=metadados["nome_entidade"],
                        documento=metadados["codigo_documento"],
                        placa=placa,
                        total_paginas_origem=total_paginas,
                        primeira_pagina=primeira_pagina,
                        pagina_placa=pagina_placa,
                        pagina_resumo=pagina_resumo,
                        pagina_validacao=pagina_validacao,
                        paginas_finais=paginas_finais,
                        paginas_saida=paginas_saida,
                        arquivo_saida=arquivo_saida,
                        status=montar_status(pagina_placa, informacoes_paginas_finais),
                    )
                )
            except Exception as erro_saida:
                resultados.append(
                    montar_registro(
                        pdf_origem=pdf_origem,
                        grupo=grupo,
                        unidade=unidade,
                        entidade=metadados["nome_entidade"],
                        documento=metadados["codigo_documento"],
                        placa=placa,
                        total_paginas_origem=total_paginas,
                        primeira_pagina=primeira_pagina,
                        pagina_placa=pagina_placa,
                        pagina_resumo=pagina_resumo,
                        pagina_validacao=pagina_validacao,
                        paginas_finais=paginas_finais,
                        paginas_saida=paginas_saida,
                        arquivo_saida=None,
                        status=f"ERRO NA SAIDA: {erro_saida}",
                    )
                )

        return resultados
    finally:
        documento_origem.close()


def salvar_relatorio(resultados, caminho_saida):
    if resultados:
        df_relatorio = pd.DataFrame(resultados).reindex(columns=COLUNAS_RELATORIO)
    else:
        df_relatorio = pd.DataFrame(columns=COLUNAS_RELATORIO)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_relatorio.to_excel(caminho_saida, index=False)
    return df_relatorio


def gerar_zip_final():
    base_zip = PASTA_OUTPUT_FINAL / "pacote_documentos_processados"
    caminho_zip = base_zip.with_suffix(".zip")

    shutil.make_archive(
        str(base_zip),
        "zip",
        root_dir=str(PASTA_PDFS_PROCESSADOS),
    )

    return caminho_zip


def executar_fluxo():
    preparar_pastas_saida()
    limpar_arquivos_anteriores()

    arquivos_pdf = listar_pdfs_disponiveis()
    print("Total de PDFs de input:", len(arquivos_pdf))

    resultados = []
    inicio_execucao = time.time()

    for indice_arquivo, caminho_pdf in enumerate(
        tqdm(arquivos_pdf, desc="Processando PDFs"),
        start=1,
    ):
        inicio_arquivo = time.time()

        try:
            resultados.extend(processar_documento_pdf(caminho_pdf))
            print(f"Concluido {caminho_pdf.name} em {time.time() - inicio_arquivo:.2f}s")

            if SALVAR_CHECKPOINT_A_CADA and indice_arquivo % SALVAR_CHECKPOINT_A_CADA == 0:
                caminho_checkpoint = PASTA_OUTPUT_TMP / "checkpoint_processamento.xlsx"
                salvar_relatorio(resultados, caminho_checkpoint)
                print(f"Checkpoint salvo apos {indice_arquivo} PDFs.")
        except Exception as erro_pdf:
            resultados.append(
                montar_registro(
                    pdf_origem=caminho_pdf.name,
                    grupo="ERRO",
                    unidade=None,
                    entidade=None,
                    documento=None,
                    placa=None,
                    total_paginas_origem=None,
                    primeira_pagina=None,
                    pagina_placa=None,
                    pagina_resumo=None,
                    pagina_validacao=None,
                    paginas_finais=[],
                    paginas_saida=[],
                    arquivo_saida=None,
                    status=f"ERRO NO PDF: {erro_pdf}",
                )
            )

    caminho_relatorio_final = PASTA_OUTPUT_FINAL / "relatorio_processamento_documentos.xlsx"
    df_relatorio = salvar_relatorio(resultados, caminho_relatorio_final)

    print(df_relatorio.head())
    if not df_relatorio.empty:
        print(df_relatorio["STATUS"].value_counts(dropna=False))
    else:
        print("Nenhum resultado foi gerado.")

    print("Relatorio final salvo em:", caminho_relatorio_final)
    print("Total de registros:", len(df_relatorio))

    if CRIAR_ZIP_FINAL:
        print("Criando pacote ZIP...")
        caminho_zip = gerar_zip_final()
        print("ZIP criado:", caminho_zip)

    fim_execucao = time.time()
    print(f"Tempo total: {(fim_execucao - inicio_execucao) / 60:.2f} minutos")


if __name__ == "__main__":
    executar_fluxo()
