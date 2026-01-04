import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import datetime
import os
import csv
import pandas as pd
from usuarios import USUARIOS

# =============================
# CONFIGURAÇÃO
# =============================
st.set_page_config(page_title="Gota de Água", layout="centered")

# =============================
# LOGIN
# =============================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login - Gota de Água")

    with st.form("login_form"):
        user = st.text_input("Utilizador")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            if user in USUARIOS and USUARIOS[user] == senha:
                st.session_state.logado = True
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Utilizador ou senha incorretos")

    st.stop()

# =============================
# APP
# =============================
st.title("🛍️ Gota de Água - Sistema de Vendas")

cliente = st.text_input("Nome do Cliente")
cambio = st.number_input("Câmbio (€ → Kz)", min_value=0.0, step=1.0)

forma_pagamento = st.radio(
    "Forma de pagamento",
    ["Não definido", "50%", "100%"],
    horizontal=True
)

# =============================
# ARTIGOS
# =============================
if "artigos" not in st.session_state:
    st.session_state.artigos = [{"nome": "", "qtd": 1, "preco": 0.0}]

st.subheader("🧾 Artigos")

for i, a in enumerate(st.session_state.artigos):
    c1, c2, c3, c4 = st.columns([4, 2, 3, 1])

    a["nome"] = c1.text_input("Artigo", a["nome"], key=f"n{i}", label_visibility="collapsed")
    a["qtd"] = c2.number_input("Qtd", min_value=1, value=a["qtd"], key=f"q{i}", label_visibility="collapsed")
    a["preco"] = c3.number_input("Preço €", min_value=0.0, step=0.5, value=a["preco"], key=f"p{i}", label_visibility="collapsed")

    if c4.button("❌", key=f"d{i}"):
        st.session_state.artigos.pop(i)
        st.rerun()

if st.button("➕ Adicionar artigo"):
    st.session_state.artigos.append({"nome": "", "qtd": 1, "preco": 0.0})
    st.rerun()

# =============================
# CÁLCULOS
# =============================
total_euro = sum(a["qtd"] * a["preco"] for a in st.session_state.artigos if a["nome"])
total_kwanza = total_euro * cambio

if forma_pagamento == "100%":
    pago = total_kwanza
    divida = 0
    estado = "PAGO"
elif forma_pagamento == "50%":
    pago = total_kwanza / 2
    divida = total_kwanza / 2
    estado = "PENDENTE (50%)"
else:
    pago = 0
    divida = total_kwanza
    estado = "NÃO DEFINIDO"

# =============================
# RESUMO
# =============================
st.subheader("📌 Resumo")
st.write(f"Total €: {total_euro:.2f}")
st.write(f"Total Kz: {total_kwanza:.2f}")
st.write(f"Pago: {pago:.2f}")
st.write(f"Dívida: {divida:.2f}")
st.write(f"Estado: {estado}")

# =============================
# GERAR FATURA (PDF + CSV)
# =============================
if st.button("📄 Gerar Fatura"):
    if not cliente or total_euro == 0:
        st.error("Preenche cliente e artigos.")
    else:
        try:
            os.makedirs("dados", exist_ok=True)
            os.makedirs("faturas", exist_ok=True)

            data = datetime.date.today()
            mes_ano= data.strftime("%Y-%m")

            pdf = f"faturas/fatura_{cliente.replace(' ', '_')}_{data}.pdf"

            # -------- PDF --------
            c = canvas.Canvas(pdf, pagesize=A4)
            y = 820

            # LOGOTIPO
            try:
                c.drawImage("logo.png", 50, y - 60, width=100, height=50)
            except:
                pass  # se não existir, ignora

            c.setFont("Helvetica-Bold", 14)
            c.drawString(200, y - 30, "GOTA DE ÁGUA ")

            c.setFont("Helvetica", 11)
            y -= 100
            c.drawString(50, y, f"Cliente: {cliente}")
            y -= 20
            c.drawString(50, y, f"Data: {data}")
            y -= 30

            for a in st.session_state.artigos:
                if a["nome"]:
                    c.drawString(60, y, f'{a["qtd"]} x {a["nome"]} - {a["preco"]:.2f} €')
                    y -= 20

            y -= 20
            c.drawString(50, y, f"Total (€): {total_euro:.2f}")
            y -= 20
            c.drawString(50, y, f"Total (Kz): {total_kwanza:.2f}")
            y -= 20
            c.drawString(50, y, f"Pago: {pago:.2f}")
            y -= 20
            c.drawString(50, y, f"Dívida: {divida:.2f}")
            y -= 20
            c.drawString(50, y, f"Estado: {estado}")

            c.save()

            # -------- CSV --------
            arquivo = "dados/vendas.csv"
            novo = not os.path.isfile(arquivo)

            with open(arquivo, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if novo:
                    w.writerow([
                        "Data", "MesAno", "Cliente",
                        "Total Euro", "Cambio", "Total Kz",
                        "Pago", "Divida", "Estado", "Vendedor"
                    ])
                w.writerow([
                    data, mes_ano, cliente,
                    total_euro, cambio, total_kwanza,
                    pago, divida, estado,
                    st.session_state.usuario
                ])

            st.session_state.ultimo_pdf = pdf
            st.success("✅ Fatura gerada e registada no histórico!")
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao gerar fatura: {e}")

# =============================
# DOWNLOAD PDF
# =============================
if "ultimo_pdf" in st.session_state and os.path.isfile(st.session_state.ultimo_pdf):
    with open(st.session_state.ultimo_pdf, "rb") as f:
        st.download_button(
            "⬇️ Baixar Fatura PDF",
            f,
            file_name=os.path.basename(st.session_state.ultimo_pdf),
            mime="application/pdf"
        )
# =============================
# HISTÓRICO DE VENDAS (CORRIGIDO)
# =============================
st.subheader("📊 Histórico Mensal")

if os.path.isfile("dados/vendas.csv"):
    df = pd.read_csv("dados/vendas.csv")

    # 🔧 CONVERSÃO FORÇADA (chave da solução)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["MesAno"] = df["Data"].dt.strftime("%Y-%m")

    # remove linhas inválidas (NaN)
    df = df.dropna(subset=["MesAno"])

    # guarda CSV limpo
    df.to_csv("dados/vendas.csv", index=False)

    meses = sorted(df["MesAno"].unique())

    for mes in meses:
        grupo = df[df["MesAno"] == mes]

        st.markdown(f"### 📅 {mes}")
        st.dataframe(grupo)

        total_mes = grupo["Total Kz"].sum()
        st.markdown(f"**💰 Total do mês:** {total_mes:.2f} Kz")


# =============================
# ELIMINAR VENDA
# =============================
st.subheader("🗑️ Eliminar Venda")

if os.path.isfile("dados/vendas.csv"):
    df = pd.read_csv("dados/vendas.csv")
    idx = st.selectbox("Venda", df.index)

    if st.button("Eliminar"):
        df.drop(idx).to_csv("dados/vendas.csv", index=False)
        st.success("Venda eliminada.")
        st.rerun()