import math
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "1234"


@app.route("/")
def home():
  return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
  nome = request.form.get("nome")
  senha = request.form.get("senha")

  if nome == "admin" and senha == "1234":
    return render_template("usuarios.html")
  else:
    return redirect("/")


@app.route("/calcular", methods=["GET", "POST"])
def calcular():
  try:
    # Se o usuário acessou via GET (clicou em voltar), reutilizamos os dados temporários se existirem
    if request.method == "GET":
      info_projeto = globals().get("dados_projeto_temporarios", None)
      if info_projeto:
        return render_template(
            "resultado.html",
            n_mod=info_projeto["n_mod"],
            pfv_real=info_projeto["pfv_real"],
            consumo_medio=info_projeto.get("consumo_medio", 0.0),
            porcentagem_potencia=info_projeto.get("porcentagem_potencia", 100.0),
            custo_paineis=info_projeto.get("custo_paineis", 0.0),
        )
      else:
        return redirect("/")

    # 1. Capturar o consumo dos 12 meses do formulário (via POST)
    meses = [
        "jan",
        "fev",
        "mar",
        "abr",
        "mai",
        "jun",
        "jul",
        "ago",
        "set",
        "out",
        "nov",
        "dez",
    ]
    consumo_total = 0

    for mes in meses:
      val_str = request.form.get(f"mes_{mes}", "0").replace(",", ".")
      valor = float(val_str) if val_str else 0.0
      consumo_total += valor

    consumo_medio_mensal = consumo_total / 12.0
    htot_anual = float(request.form.get("htot_anual", "0").replace(",", "."))
    modelo_painel = request.form.get("modelo_painel", "canadian_550")

    # --- CATÁLOGO TÉCNICO DOS PAINÉIS ---
    catalogo_paineis = {
        "canadian_550": {
            "nome": "Painel Solar 550W Canadian (CS6W-550MS)",
            "pmpp": 550.0,
            "vmpp": 41.6,
            "impp": 13.23,
            "voc": 49.3,
            "isc": 14.00,
            "preco": 600.00,
        },
        "maxeon_410": {
            "nome": "Painel Solar 410W Maxeon 3 (SPR-MAX3-410)",
            "pmpp": 410.0,
            "vmpp": 72.9,
            "impp": 5.63,
            "voc": 85.3,
            "isc": 6.01,
            "preco": 500.00,
        },
    }

    painel_selecionado = catalogo_paineis.get(
        modelo_painel, catalogo_paineis["canadian_550"]
    )
    PMOD_PADRAO = painel_selecionado["pmpp"]
    rendimento_global = 0.80

    if htot_anual > 0:
      pfv_teorica = (consumo_medio_mensal * 1000) / (
          htot_anual * 30 * rendimento_global
      )
    else:
      pfv_teorica = 0

    n_mod = math.ceil(pfv_teorica / PMOD_PADRAO) if PMOD_PADRAO > 0 else 0
    pfv_real = n_mod * PMOD_PADRAO
    porcentagem_potencia = (
        (pfv_real / pfv_teorica * 100) if pfv_teorica > 0 else 0
    )
    custo_paineis = n_mod * painel_selecionado["preco"]

    # Salvando dados globalmente para acesso nas próximas páginas
    global dados_projeto_temporarios
    dados_projeto_temporarios = {
        "pfv_real": pfv_real,
        "n_mod": n_mod,
        "consumo_medio": round(consumo_medio_mensal, 2),
        "porcentagem_potencia": round(porcentagem_potencia, 2),
        "painel": painel_selecionado,
        "custo_paineis": round(custo_paineis, 2),
    }

    return render_template(
        "resultado.html",
        n_mod=n_mod,
        pfv_real=pfv_real,
        consumo_medio=round(consumo_medio_mensal, 2),
        porcentagem_potencia=round(porcentagem_potencia, 2),
        custo_paineis=round(custo_paineis, 2),
    )

  except Exception as e:
    return f"Erro ao realizar o cálculo: {e}"


# Rota para a página de Inversor
@app.route("/inversor")
def inversor_pagina():
  return render_template("inversor.html")


# Rota para processar o dimensionamento do inversor
@app.route("/calcular-inversor", methods=["POST"])
def calcular_inversor():
  try:
    fator_cc_ca = float(request.form.get("fator_cc_ca", 1.20))
    tipo_rede = request.form.get("tipo_rede", "trifasico")

    info_projeto = globals().get(
        "dados_projeto_temporarios",
        {
            "pfv_real": 5500.0,
            "n_mod": 10,
            "painel": {
                "pmpp": 550,
                "vmpp": 41.6,
                "impp": 13.23,
                "voc": 49.3,
                "isc": 14.0,
                "preco": 600.00,
            },
        },
    )

    pfv_cc = info_projeto["pfv_real"]
    potencia_ca_calculada = pfv_cc / fator_cc_ca

    # --- CATÁLOGO TÉCNICO DE INVERSORES COMERCIAIS ---
    catalogo_inversores = [
        # 1 kW
        {
            "modelo": "EcoSolys ECOS1000",
            "potencia_ca": 1000,
            "max_cc": 1300,
            "rede": ["monofasico", "bifasico"],
            "mppts": 1,
            "tensao": "220V",
            "eficiencia": "97,2%",
            "preco": 1450.00,
        },
        # 2 kW
        {
            "modelo": "Growatt MIC 2000TL-X",
            "potencia_ca": 2000,
            "max_cc": 2800,
            "rede": ["monofasico", "bifasico"],
            "mppts": 1,
            "tensao": "220V",
            "eficiencia": "97,4%",
            "preco": 1850.00,
        },
        # 3 kW
        {
            "modelo": "Growatt MIC 3000TL-X2",
            "potencia_ca": 3000,
            "max_cc": 4200,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "97,6%",
            "preco": 2350.00,
        },
        {
            "modelo": "Deye SUN-3K-G04 / G05",
            "potencia_ca": 3000,
            "max_cc": 3900,
            "rede": ["monofasico", "bifasico"],
            "mppts": 1,
            "tensao": "220V",
            "eficiencia": "97,5%",
            "preco": 2250.00,
        },
        # 5 kW
        {
            "modelo": "Growatt MIN 5000TL-X",
            "potencia_ca": 5000,
            "max_cc": 7000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "98,4%",
            "preco": 3250.00,
        },
        {
            "modelo": "Deye SUN-5K-G05",
            "potencia_ca": 5000,
            "max_cc": 6500,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "97,7%",
            "preco": 3100.00,
        },
        {
            "modelo": "Sungrow SG5.0RS",
            "potencia_ca": 5000,
            "max_cc": 7500,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "97,8%",
            "preco": 3450.00,
        },
        # 6 kW
        {
            "modelo": "Deye SUN-6K-G05",
            "potencia_ca": 6000,
            "max_cc": 7800,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "97,7%",
            "preco": 3600.00,
        },
        {
            "modelo": "Growatt MIN 6000TL-X",
            "potencia_ca": 6000,
            "max_cc": 8400,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "98,4%",
            "preco": 3790.00,
        },
        # 7 kW
        {
            "modelo": "Solis 1P7K-4G",
            "potencia_ca": 7000,
            "max_cc": 9100,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "98,1%",
            "preco": 4350.00,
        },
        {
            "modelo": "Goodwe GW7000-MS",
            "potencia_ca": 7000,
            "max_cc": 10500,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,0%",
            "preco": 4500.00,
        },
        # 8 kW
        {
            "modelo": "Growatt MIN 8000TL-X",
            "potencia_ca": 8000,
            "max_cc": 11200,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,4%",
            "preco": 4950.00,
        },
        {
            "modelo": "Deye SUN-8K-G05",
            "potencia_ca": 8000,
            "max_cc": 10400,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "97,7%",
            "preco": 4750.00,
        },
        {
            "modelo": "Sungrow SG8.0RS",
            "potencia_ca": 8000,
            "max_cc": 12000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,0%",
            "preco": 5200.00,
        },
        {
            "modelo": "Solis S6-GR1P8K",
            "potencia_ca": 8000,
            "max_cc": 12000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,1%",
            "preco": 5100.00,
        },
        # 10 kW
        {
            "modelo": "Growatt MIN 10000TL-X",
            "potencia_ca": 10000,
            "max_cc": 14000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,4%",
            "preco": 5950.00,
        },
        {
            "modelo": "SAJ R6-10K-S3",
            "potencia_ca": 10000,
            "max_cc": 15000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,2%",
            "preco": 5800.00,
        },
        {
            "modelo": "Deye SUN-10K-G05",
            "potencia_ca": 10000,
            "max_cc": 13000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 2,
            "tensao": "220V",
            "eficiencia": "97,7%",
            "preco": 5650.00,
        },
        {
            "modelo": "Sungrow SG10RS",
            "potencia_ca": 10000,
            "max_cc": 15000,
            "rede": ["monofasico", "bifasico"],
            "mppts": 3,
            "tensao": "220V",
            "eficiencia": "98,0%",
            "preco": 6200.00,
        },
        # 12 kW / 15 kW (Trifásicos)
        {
            "modelo": "Growatt MID 12KTL3-X",
            "potencia_ca": 12000,
            "max_cc": 18000,
            "rede": ["trifasico"],
            "mppts": 2,
            "tensao": "220V/380V",
            "eficiencia": "98,6%",
            "preco": 6850.00,
        },
        {
            "modelo": "Deye SUN-15K-G05",
            "potencia_ca": 15000,
            "max_cc": 19500,
            "rede": ["trifasico"],
            "mppts": 2,
            "tensao": "220V/380V",
            "eficiencia": "98,5%",
            "preco": 7400.00,
        },
        {
            "modelo": "Growatt MID 15KTL3-X",
            "potencia_ca": 15000,
            "max_cc": 22500,
            "rede": ["trifasico"],
            "mppts": 2,
            "tensao": "220V/380V",
            "eficiencia": "98,6%",
            "preco": 7650.00,
        },
    ]

    # Filtra inversores que atendem à potência CA e suportam a potência CC (ordenados do menor para o maior)
    candidatos = [
        inv
        for inv in catalogo_inversores
        if inv["potencia_ca"] >= potencia_ca_calculada and inv["max_cc"] >= pfv_cc
    ]

    if not candidatos:
      candidatos = [catalogo_inversores[-1]]

    # Pega estritamente a MENOR potência comercial suficiente (o modelo ideal mais próximo)
    potencia_ideal = min(inv["potencia_ca"] for inv in candidatos)
    modelos_recomendados = [
        inv for inv in candidatos if inv["potencia_ca"] == potencia_ideal
    ]

    inversor_kw = potencia_ideal / 1000.0
    modelo_destaque = modelos_recomendados[0]["modelo"]

    # Salva o inversor principal nos dados temporários para o financeiro
    info_projeto["inversor_principal"] = modelos_recomendados[0]

    return render_template(
        "resultado_inversor.html",
        potencia_cc=pfv_cc,
        potencia_calculada=round(potencia_ca_calculada, 2),
        inversor_sugerido=f"{inversor_kw} kW - {modelo_destaque}",
        fator_cc=fator_cc_ca,
        painel=info_projeto["painel"],
        modelos_recomendados=modelos_recomendados,
    )

  except Exception as e:
    return f"Erro ao calcular inversor: {e}"


# Rota para a página de Análise Financeira
@app.route("/financia")
def financia_pagina():
  # Recupera os dados temporários do projeto
  info_projeto = globals().get("dados_projeto_temporarios", {})

  # 1. Custo dos painéis (calculado no dimensionamento)
  custo_paineis = float(info_projeto.get("custo_paineis", 4800.00))

  # 2. Custo do inversor escolhido na etapa anterior
  inversor_info = info_projeto.get("inversor_principal", {})
  custo_inversor = float(inversor_info.get("preco", 3250.00))

  # 3. Materiais de instalação (cabos, conectores, string box, estrutura de fixação)
  n_mod = int(info_projeto.get("n_mod", 8))
  custo_materiais = n_mod * 80.00

  # 4. Mão de obra de instalação e homologação
  pfv_real = float(info_projeto.get("pfv_real", 4400.00))
  custo_mao_de_obra = max(1500.00, (pfv_real / 1000.0) * 350.00)

  # Investimento Inicial Total (CAPEX automático arredondado)
  capex_total = round(
      custo_paineis + custo_inversor + custo_materiais + custo_mao_de_obra, 2
  )

  return render_template("financia.html", investimento_automatico=capex_total)


@app.route("/calcular-financia", methods=["POST"])
def calcular_financia():
  try:
    # Tratamento robusto do Investimento Inicial
    inv_raw = request.form.get("investimento", "10000")
    inv_str = (
        str(inv_raw).replace("R$", "").replace(".", "").replace(",", ".").strip()
    )
    investimento = float(inv_str) if inv_str else 10000.0

    # Tratamento da Média Mensal da Conta de Luz (R$/mês)
    media_raw = request.form.get("media_conta_mensal", "450")
    media_str = (
        str(media_raw)
        .replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    media_conta_mensal = float(media_str) if media_str else 450.0

    # Tratamento da Taxa Mínima (30, 50 ou 100 kWh)
    taxa_raw = request.form.get("taxa_minima", "100")
    taxa_str = str(taxa_raw).replace(",", ".").strip()
    taxa_minima = float(taxa_str) if taxa_str else 100.0

    # Recupera dados temporários do projeto
    info_projeto = globals().get("dados_projeto_temporarios", {})
    pfv_real = float(info_projeto.get("pfv_real", 4400.0))
    consumo_medio_mensal = float(info_projeto.get("consumo_medio", 500.0))

    # Descobre a tarifa média (R$/kWh) dividindo a média mensal em R$ pelo consumo médio em kWh
    tarifa_media = (
        (media_conta_mensal / consumo_medio_mensal)
        if consumo_medio_mensal > 0
        else 0.95
    )

    # Geração média mensal estimada (kWh/mês)
    geracao_mensal = (pfv_real / 1000.0) * 135.0

    # Consumo líquido cobrado respeitando a taxa mínima de disponibilidade
    consumo_liquido = max(consumo_medio_mensal - geracao_mensal, taxa_minima)

    # Novo cálculo do valor da conta pós-solar (R$/mês)
    nova_conta_mensal = consumo_liquido * tarifa_media

    # Economia financeira mensal e anual
    economia_mensal = (consumo_medio_mensal - consumo_liquido) * tarifa_media
    economia_anual_total = economia_mensal * 12.0

    # Garantia de segurança caso a economia fique zerada ou negativa
    if economia_anual_total <= 0:
      economia_anual_total = geracao_mensal * 12.0 * tarifa_media

    # Cálculo do Payback Simples (anos)
    payback_calculado = (
        investimento / economia_anual_total if economia_anual_total > 0 else 0.0
    )

    # Projeção do Fluxo de Caixa Acumulado (0 a 30 anos) com reajuste tarifário de 5% a.a.
    anos_grafico = [f"Ano {i}" for i in range(31)]
    fluxo_acumulado = []
    saldo = -investimento

    for ano in range(31):
      fluxo_acumulado.append(round(saldo, 2))
      economia_do_ano = economia_anual_total * ((1.05) ** ano)
      saldo += economia_do_ano

    # Guarda os resultados financeiros exatos para o relatório repetir sem recalcular
    info_projeto["financeiro"] = {
        "investimento": investimento,
        "media_conta_mensal": media_conta_mensal,
        "nova_conta_mensal": nova_conta_mensal,
        "payback_calculado": payback_calculado,
        "anos_grafico": anos_grafico,
        "fluxo_acumulado": fluxo_acumulado,
    }

    # Formatação para exibição no HTML
    investimento_fmt = (
        f"{investimento:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    payback_fmt = f"{payback_calculado:.1f}".replace(".", ",")
    fatura_antiga_fmt = (
        f"{media_conta_mensal:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    nova_conta_fmt = (
        f"{nova_conta_mensal:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return render_template(
        "resultado_financia.html",
        investimento=investimento_fmt,
        payback_simples=payback_fmt,
        fatura_antiga=fatura_antiga_fmt,
        nova_conta=nova_conta_fmt,
        anos_grafico=anos_grafico,
        fluxo_acumulado=fluxo_acumulado,
    )

  except Exception as e:
    return f"Erro detalhado no cálculo financeiro: {str(e)}"


def _parse_numero(valor, padrao=0.0):
  if valor is None or valor == "":
    return float(padrao)
  if isinstance(valor, (int, float)):
    return float(valor)
  texto = (
      str(valor)
      .strip()
      .replace("R$", "")
      .replace("Anos", "")
      .replace("anos", "")
      .strip()
  )
  if "," in texto and "." in texto:
    texto = texto.replace(".", "").replace(",", ".")
  elif "," in texto:
    texto = texto.replace(",", ".")
  try:
    return float(texto)
  except ValueError:
    return float(padrao)


def _formatar_ptbr(valor, decimais=2):
  formato = f"{float(valor):,.{decimais}f}"
  return formato.replace(",", "X").replace(".", ",").replace("X", ".")


# Rota para a Página de Relatório Geral do Projeto
@app.route("/relatorio")
def relatorio_projeto():
  # Recupera todos os dados temporários acumulados do projeto
  info_projeto = globals().get("dados_projeto_temporarios", {})
  fin = info_projeto.get("financeiro", {})

  # Extrai os dados salvos nas etapas anteriores
  n_mod = int(_parse_numero(info_projeto.get("n_mod"), 7))
  pfv_real = _parse_numero(info_projeto.get("pfv_real"), 3850.0)
  consumo_medio = _parse_numero(info_projeto.get("consumo_medio"), 350.0)

  # Pega o dicionário do painel selecionado (ex: 'nome', 'preco')
  painel = info_projeto.get(
      "painel",
      {
          "nome": "Painel Solar 550W Canadian (CS6W-550MS)",
          "pmpp": 550,
          "preco": 600.0,
      },
  )
  nome_painel_completo = painel.get("nome", "Painel Solar 550W")

  # Pega o dicionário do inversor principal selecionado
  inversor_info = info_projeto.get(
      "inversor_principal",
      {
          "modelo": "Growatt MIN 5000TL-X",
          "potencia_ca": 5000,
          "preco": 3250.0,
      },
  )

  # Custos e CAPEX
  custo_paineis = n_mod * _parse_numero(painel.get("preco"), 600.0)
  custo_inversor = _parse_numero(inversor_info.get("preco"), 3250.0)
  custo_materiais = n_mod * 80.0
  custo_mao_de_obra = max(1500.0, (pfv_real / 1000.0) * 350.0)
  capex_calculado = (
      custo_paineis + custo_inversor + custo_materiais + custo_mao_de_obra
  )

  # Reaproveita os valores exatos da análise financeira se existirem
  if fin:
    investimento_exibido = _parse_numero(fin.get("investimento"), capex_calculado)
    media_conta_mensal = _parse_numero(fin.get("media_conta_mensal"), 0.0)
    nova_conta_mensal = _parse_numero(fin.get("nova_conta_mensal"), 0.0)
    payback_calculado = _parse_numero(fin.get("payback_calculado"), 0.0)
    anos_grafico = fin.get("anos_grafico") or [f"Ano {i}" for i in range(31)]
    fluxo_acumulado = [
        _parse_numero(v, 0.0) for v in (fin.get("fluxo_acumulado") or [])
    ]
  else:
    # Fallback apenas caso o usuário acesse /relatorio sem passar por /calcular-financia
    investimento_exibido = capex_calculado
    media_conta_mensal = _parse_numero(info_projeto.get("valor_conta"), 0.0)
    tarifa_media = (
        (media_conta_mensal / consumo_medio) if consumo_medio > 0 else 0.95
    )
    geracao_mensal = (pfv_real / 1000.0) * 135.0
    consumo_liquido = max(consumo_medio - geracao_mensal, 50.0)
    nova_conta_mensal = consumo_liquido * tarifa_media
    economia_anual = ((consumo_medio - consumo_liquido) * tarifa_media) * 12.0
    if economia_anual <= 0:
      economia_anual = geracao_mensal * 12.0 * tarifa_media
    payback_calculado = (
        (investimento_exibido / economia_anual) if economia_anual > 0 else 0.0
    )
    anos_grafico = [f"Ano {i}" for i in range(31)]
    fluxo_acumulado = []
    saldo = -investimento_exibido
    for ano in range(31):
      fluxo_acumulado.append(round(saldo, 2))
      economia_do_ano = economia_anual * ((1.05) ** ano)
      saldo += economia_do_ano

  potencia_ca_kw = _parse_numero(inversor_info.get("potencia_ca"), 0.0) / 1000.0

  return render_template(
      "relatorio.html",
      n_mod=n_mod,
      potencia_pico=_formatar_ptbr(pfv_real, 1),
      nome_painel=nome_painel_completo,
      preco_unit_painel=_formatar_ptbr(painel.get("preco", 0), 2),
      custo_total_paineis=_formatar_ptbr(custo_paineis, 2),
      modelo_inversor=inversor_info.get("modelo", "Inversor Solar"),
      potencia_inversor=_formatar_ptbr(potencia_ca_kw, 1),
      preco_inversor=_formatar_ptbr(inversor_info.get("preco", 0), 2),
      capex_total=_formatar_ptbr(investimento_exibido, 2),
      payback_simples=_formatar_ptbr(payback_calculado, 1),
      fatura_antiga=_formatar_ptbr(media_conta_mensal, 2),
      nova_conta=_formatar_ptbr(nova_conta_mensal, 2),
      anos_grafico=anos_grafico,
      fluxo_acumulado=fluxo_acumulado,
  )


if __name__ == "__main__":
  app.run(debug=True)