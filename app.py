import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
import gspread
import json
from datetime import datetime
import numpy as np

# ─── Configuração da página ───
st.set_page_config(
    page_title="Dashboard de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Configuração fixa da planilha ───
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1PnZtUVbwFWOmonSysb0YDfHgpfWsA1r-VkGgUy8-Xh8/edit?gid=302051685#gid=302051685"
SHEET_NAME = "Dados WhatsApp"

# ─── Estilos CSS ───
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card h2 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 700;
    }
    .metric-card p {
        font-size: 0.9rem;
        margin: 5px 0 0 0;
        opacity: 0.9;
    }
    .card-qualificado {background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);}
    .card-convertido {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}
    .card-desqualificado {background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);}
    .card-achei {background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);}
    .card-nao-interagiu {background: linear-gradient(135deg, #6c757d 0%, #adb5bd 100%);}
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 0.5rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #667eea;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# ─── Cores padrão para qualificação ───
CORES_QUALIFICACAO = {
    "Qualificado": "#38ef7d",
    "Convertido": "#764ba2",
    "Desqualificado": "#f45c43",
    "Achei": "#ffd200",
    "Não interagiu": "#adb5bd",
}

STATUS_ORDER = ["Qualificado", "Convertido", "Desqualificado", "Achei", "Não interagiu"]


# ─── Funções de conexão e dados ───
@st.cache_data(ttl=300)
def carregar_dados() -> pd.DataFrame:
    """Carrega dados do Google Sheets usando credenciais do secrets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    credentials_info = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    worksheet = spreadsheet.worksheet(SHEET_NAME)

    # Usar get_all_values() para evitar erro de NA
    all_values = worksheet.get_all_values()

    if len(all_values) < 2:
        return pd.DataFrame()

    headers = all_values[0]
    rows = all_values[1:]

    df = pd.DataFrame(rows, columns=headers)
    return df


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e prepara os dados para análise."""
    df = df.copy()

    # Converter todas as colunas para string primeiro
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # Converter coluna de data
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, format="mixed", errors="coerce")

    # Remover linhas sem data válida
    df = df.dropna(subset=["data"])

    # Limpar qualificação
    df["qualificacao"] = df["qualificacao"].str.strip()
    df = df[df["qualificacao"].isin(STATUS_ORDER)].copy()

    # Dia da semana
    dias_map = {
        0: "Segunda", 1: "Terça", 2: "Quarta",
        3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo",
    }
    df["dia_semana"] = df["data"].dt.dayofweek.map(dias_map)
    df["hora"] = df["data"].dt.hour

    # Limpar UTMs
    for col in ["utm_campaign", "utm_source", "utm_medium", "utm_term"]:
        if col in df.columns:
            df[col] = df[col].replace({"": "Não informado", "nan": "Não informado", "None": "Não informado"})

    # Limpar CEP
    if "cep" in df.columns:
        df["cep"] = df["cep"].str.replace(r"\D", "", regex=True)
        df["cep"] = df["cep"].replace({"": "Não informado", "nan": "Não informado"})

    # Limpar valor
    if "valor" in df.columns:
        df["valor"] = df["valor"].replace({"": "0", "nan": "0", "None": "0"})
        df["valor"] = pd.to_numeric(
            df["valor"].str.replace(r"[^\d.,]", "", regex=True).str.replace(",", "."),
            errors="coerce"
        ).fillna(0)

    return df


# ─── Carregar dados automaticamente ───
st.title("📊 Dashboard de Leads")

try:
    with st.spinner("Conectando ao Google Sheets..."):
        raw = carregar_dados()
        df = preparar_dados(raw)
        st.sidebar.success(f"✅ {len(df)} registros carregados!")
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {e}")
    st.info("Verifique se as credenciais do Google estão configuradas corretamente nas Secrets do Streamlit.")
    st.stop()

# ─── Sidebar — Filtros ───
st.sidebar.image("https://img.icons8.com/fluency/96/combo-chart.png", width=60)
st.sidebar.title("🔍 Filtros")

if st.sidebar.button("🔄 Recarregar Dados", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Filtro de data
col_data_min, col_data_max = st.sidebar.columns(2)
data_min = df["data"].min().date() if pd.notna(df["data"].min()) else datetime(2024, 1, 1).date()
data_max = df["data"].max().date() if pd.notna(df["data"].max()) else datetime.today().date()

with col_data_min:
    filtro_data_inicio = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
with col_data_max:
    filtro_data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)

filtro_qualificacao = st.sidebar.multiselect(
    "Qualificação", options=STATUS_ORDER, default=STATUS_ORDER,
)

campanhas_disponiveis = sorted(df["utm_campaign"].unique().tolist())
filtro_campanha = st.sidebar.multiselect(
    "Campanhas", options=campanhas_disponiveis, default=campanhas_disponiveis,
)

mask = (
    (df["data"].dt.date >= filtro_data_inicio)
    & (df["data"].dt.date <= filtro_data_fim)
    & (df["qualificacao"].isin(filtro_qualificacao))
    & (df["utm_campaign"].isin(filtro_campanha))
)
df_filtrado = df[mask].copy()

st.caption(f"Período: {filtro_data_inicio.strftime('%d/%m/%Y')} a {filtro_data_fim.strftime('%d/%m/%Y')} · {len(df_filtrado)} registros")

# ══════════════════════════════════════════════════════════════
# 1. MÉTRICAS GERAIS
# ══════════════════════════════════════════════════════════════
st.markdown('<p class="section-header">📌 1. Quantidade de Contatos por Qualificação</p>', unsafe_allow_html=True)

total = len(df_filtrado)
contagem = df_filtrado["qualificacao"].value_counts()

cols = st.columns(6)
with cols[0]:
    st.markdown(f"""
    <div class="metric-card card-convertido">
        <h2>{total}</h2>
        <p>Total de Contatos</p>
    </div>""", unsafe_allow_html=True)

css_map = {
    "Qualificado": "card-qualificado",
    "Convertido": "card-convertido",
    "Desqualificado": "card-desqualificado",
    "Achei": "card-achei",
    "Não interagiu": "card-nao-interagiu",
}
for i, status in enumerate(STATUS_ORDER):
    with cols[i + 1]:
        valor = contagem.get(status, 0)
        st.markdown(f"""
        <div class="metric-card {css_map[status]}">
            <h2>{valor}</h2>
            <p>{status}</p>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 2. MAPA DE CALOR
# ══════════════════════════════════════════════════════════════
st.markdown('<p class="section-header">🔥 2. Mapa de Calor — Conversões por Dia da Semana e Hora</p>', unsafe_allow_html=True)

dias_ordem = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

heatmap_data = df_filtrado.groupby(["dia_semana", "hora"]).size().reset_index(name="quantidade")
heatmap_pivot = heatmap_data.pivot_table(
    index="dia_semana", columns="hora", values="quantidade", fill_value=0
)
heatmap_pivot = heatmap_pivot.reindex(dias_ordem).fillna(0)

fig_heat = px.imshow(
    heatmap_pivot.values,
    x=[f"{h}h" for h in heatmap_pivot.columns],
    y=heatmap_pivot.index.tolist(),
    color_continuous_scale="YlOrRd",
    labels=dict(x="Hora do Dia", y="Dia da Semana", color="Leads"),
    aspect="auto",
)
fig_heat.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), font=dict(size=12))
st.plotly_chart(fig_heat, use_container_width=True)

resumo_dia = df_filtrado.groupby("dia_semana").size().reset_index(name="Total")
resumo_dia = resumo_dia.set_index("dia_semana").reindex(dias_ordem).reset_index()
resumo_dia.columns = ["Dia da Semana", "Total de Leads"]

col_heat1, col_heat2 = st.columns([2, 1])
with col_heat2:
    st.dataframe(resumo_dia, use_container_width=True, hide_index=True)
with col_heat1:
    fig_bar_dia = px.bar(
        resumo_dia, x="Dia da Semana", y="Total de Leads",
        color="Total de Leads", color_continuous_scale="YlOrRd", text_auto=True,
    )
    fig_bar_dia.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_bar_dia, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 3. QUALIFICAÇÃO POR CAMPANHA
# ══════════════════════════════════════════════════════════════
st.markdown('<p class="section-header">📈 3. Status de Qualificação por Campanha</p>', unsafe_allow_html=True)

camp_qual = df_filtrado.groupby(["utm_campaign", "qualificacao"]).size().reset_index(name="quantidade")

if not camp_qual.empty:
    fig_camp = px.bar(
        camp_qual, x="utm_campaign", y="quantidade", color="qualificacao",
        color_discrete_map=CORES_QUALIFICACAO, barmode="group", text_auto=True,
        labels={"utm_campaign": "Campanha", "quantidade": "Leads", "qualificacao": "Qualificação"},
        category_orders={"qualificacao": STATUS_ORDER},
    )
    fig_camp.update_layout(
        height=450, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig_camp, use_container_width=True)

    tabela_camp = camp_qual.pivot_table(
        index="utm_campaign", columns="qualificacao", values="quantidade", fill_value=0
    ).reset_index()
    tabela_camp.columns.name = None
    cols_order = ["utm_campaign"] + [s for s in STATUS_ORDER if s in tabela_camp.columns]
    tabela_camp = tabela_camp[cols_order]
    tabela_camp["Total"] = tabela_camp[[s for s in STATUS_ORDER if s in tabela_camp.columns]].sum(axis=1)
    tabela_camp = tabela_camp.sort_values("Total", ascending=False)
    tabela_camp = tabela_camp.rename(columns={"utm_campaign": "Campanha"})
    st.dataframe(tabela_camp, use_container_width=True, hide_index=True)
else:
    st.warning("Nenhum dado de campanha encontrado.")

# ══════════════════════════════════════════════════════════════
# 4. GOOGLE ADS
# ══════════════════════════════════════════════════════════════
st.markdown('<p class="section-header">🔎 4. Google Ads — Qualificação e Termos de Pesquisa</p>', unsafe_allow_html=True)

df_google = df_filtrado[df_filtrado["utm_source"].str.lower() == "google"].copy()

if not df_google.empty:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Qualificação — Leads do Google**")
        google_qual = df_google["qualificacao"].value_counts().reset_index()
        google_qual.columns = ["Qualificação", "Quantidade"]
        fig_google_pie = px.pie(
            google_qual, names="Qualificação", values="Quantidade",
            color="Qualificação", color_discrete_map=CORES_QUALIFICACAO, hole=0.45,
        )
        fig_google_pie.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_google_pie, use_container_width=True)

    with col_g2:
        st.markdown("**Leads do Google por Campanha**")
        google_camp = df_google.groupby(["utm_campaign", "qualificacao"]).size().reset_index(name="quantidade")
        fig_google_camp = px.bar(
            google_camp, x="utm_campaign", y="quantidade", color="qualificacao",
            color_discrete_map=CORES_QUALIFICACAO, barmode="stack", text_auto=True,
            labels={"utm_campaign": "Campanha", "quantidade": "Leads", "qualificacao": "Qualificação"},
            category_orders={"qualificacao": STATUS_ORDER},
        )
        fig_google_camp.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_google_camp, use_container_width=True)

    st.markdown("**Termos de Pesquisa (utm_term) por Status de Qualificação**")
    termos_qual = df_google.groupby(["utm_term", "qualificacao"]).size().reset_index(name="quantidade")
    termos_qual = termos_qual[termos_qual["utm_term"] != "Não informado"]

    if not termos_qual.empty:
        fig_termos = px.bar(
            termos_qual, x="quantidade", y="utm_term", color="qualificacao",
            color_discrete_map=CORES_QUALIFICACAO, orientation="h", text_auto=True,
            labels={"utm_term": "Termo", "quantidade": "Leads", "qualificacao": "Qualificação"},
            category_orders={"qualificacao": STATUS_ORDER},
        )
        fig_termos.update_layout(
            height=max(400, len(termos_qual["utm_term"].unique()) * 30),
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(categoryorder="total ascending"),
        )
        st.plotly_chart(fig_termos, use_container_width=True)

        tabela_termos = termos_qual.pivot_table(
            index="utm_term", columns="qualificacao", values="quantidade", fill_value=0
        ).reset_index()
        tabela_termos.columns.name = None
        cols_t = ["utm_term"] + [s for s in STATUS_ORDER if s in tabela_termos.columns]
        tabela_termos = tabela_termos[cols_t]
        tabela_termos["Total"] = tabela_termos[[s for s in STATUS_ORDER if s in tabela_termos.columns]].sum(axis=1)
        tabela_termos = tabela_termos.sort_values("Total", ascending=False)
        tabela_termos = tabela_termos.rename(columns={"utm_term": "Termo de Pesquisa"})
        st.dataframe(tabela_termos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum termo de pesquisa (utm_term) encontrado para leads do Google.")
else:
    st.warning("Nenhum lead com utm_source = 'google' encontrado.")

# ══════════════════════════════════════════════════════════════
# 5. CEPs
# ══════════════════════════════════════════════════════════════
st.markdown('<p class="section-header">📍 5. Análise de CEPs por Qualificação</p>', unsafe_allow_html=True)

df_cep = df_filtrado[df_filtrado["cep"] != "Não informado"].copy()

if not df_cep.empty:
    cep_qual = df_cep.groupby(["cep", "qualificacao"]).size().reset_index(name="quantidade")

    top_n = st.slider("Quantidade de CEPs a exibir", min_value=5, max_value=50, value=15, step=5)
    top_ceps = df_cep["cep"].value_counts().head(top_n).index.tolist()
    cep_qual_top = cep_qual[cep_qual["cep"].isin(top_ceps)]

    fig_cep = px.bar(
        cep_qual_top, x="cep", y="quantidade", color="qualificacao",
        color_discrete_map=CORES_QUALIFICACAO, barmode="stack", text_auto=True,
        labels={"cep": "CEP", "quantidade": "Leads", "qualificacao": "Qualificação"},
        category_orders={"qualificacao": STATUS_ORDER},
    )
    fig_cep.update_layout(
        height=450, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(categoryorder="total descending", type="category"),
    )
    st.plotly_chart(fig_cep, use_container_width=True)

    tabela_cep = cep_qual.pivot_table(
        index="cep", columns="qualificacao", values="quantidade", fill_value=0
    ).reset_index()
    tabela_cep.columns.name = None
    cols_c = ["cep"] + [s for s in STATUS_ORDER if s in tabela_cep.columns]
    tabela_cep = tabela_cep[cols_c]
    tabela_cep["Total"] = tabela_cep[[s for s in STATUS_ORDER if s in tabela_cep.columns]].sum(axis=1)
    tabela_cep = tabela_cep.sort_values("Total", ascending=False)
    tabela_cep = tabela_cep.rename(columns={"cep": "CEP"})
    st.dataframe(tabela_cep, use_container_width=True, hide_index=True)
else:
    st.warning("Nenhum CEP informado encontrado nos dados.")

# ─── Footer ───
st.markdown("---")
st.caption("Dashboard de Leads · Desenvolvido com Streamlit + Google Sheets API")
