import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA (Interface do Usuário)
# ==============================================================================
st.set_page_config(
    page_title="Cyberkayzen - Dashboard Logístico",
    page_icon="🚚",
    layout="wide"
)

# Estilização CSS básica para melhorar o visual
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIMULAÇÃO DA BASE DE DADOS (Substitua pelo seu arquivo real se necessário)
# ==============================================================================
@st.cache_data
def carregar_dados():
    np.random.seed(42)
    n_registros = 200
    
    # Gerando datas
    data_base = datetime(2026, 5, 1)
    datas_prometidas = [data_base + timedelta(days=int(np.random.randint(1, 30))) for _ in range(n_registros)]
    
    # Criando atrasos propositais (alguns entregues no prazo, outros atrasados, outros pendentes)
    datas_efetivas = []
    for dt in datas_prometidas:
        sorteio = np.random.rand()
        if sorteio < 0.6:  # No prazo
            datas_efetivas.append(dt - timedelta(days=int(np.random.randint(0, 2))))
        elif sorteio < 0.85:  # Atrasado
            datas_efetivas.append(dt + timedelta(days=int(np.random.randint(1, 10))))
        else:  # Ainda não entregue (Pendente)
            datas_efetivas.append(None)

    dados = {
        'ID_Pedido': [f"REQ{i:04d}" for i in range(1, n_registros + 1)],
        'Data_Prometida': datas_prometidas,
        'Data_Efetiva': datas_efetivas,
        'Transportadora': np.random.choice(['TransRapido', 'LogBrasil', 'LevaETrás', 'VanteLog'], n_registros),
        'Regiao': np.random.choice(['Sudeste', 'Nordeste', 'Sul', 'Centro-Oeste', 'Norte'], n_registros, p=[0.4, 0.2, 0.2, 0.1, 0.1]),
        'Valor_Carga': np.random.round(np.random.uniform(500, 15000, n_registros), 2)
    }
    
    df = pd.DataFrame(dados)
    
    # --------------------------------------------------------------------------
    # REQUISITO II: CÁLCULOS E LÓGICA DE ATRASO
    # --------------------------------------------------------------------------
    # Data de referência para os cálculos (Simulando o "Hoje" como 11/06/2026)
    hoje = pd.to_datetime('2026-06-11')
    df['Data_Prometida'] = pd.to_datetime(df['Data_Prometida'])
    df['Data_Efetiva'] = pd.to_datetime(df['Data_Efetiva'])
    
    # Cálculo dos Dias de Atraso
    # Se já entregou, calcula a diferença. Se não entregou e já passou do prazo, calcula baseado no 'Hoje'.
    df['Dias_Atraso'] = df.apply(
        lambda r: (r['Data_Efetiva'] - r['Data_Prometida']).days if pd.notnull(r['Data_Efetiva'])
        else (hoje - r['Data_Prometida']).days if hoje > r['Data_Prometida'] else 0, axis=1
    )
    # Ajusta para não negativar dias em entregas adiantadas
    df['Dias_Atraso'] = df['Dias_Atraso'].clip(lower=0)
    
    # Identificação do Status (Requisito I)
    df['Status'] = df.apply(
        lambda r: 'Atrasado' if r['Dias_Atraso'] > 0
        else 'Pendente no Prazo' if pd.isnull(r['Data_Efetiva'])
        else 'No Prazo', axis=1
    )
    
    return df

df_original = carregar_dados()

# ==============================================================================
# TÍTULO E FILTROS (Recursos de Análise)
# ==============================================================================
st.title("🚚 Dashboard de Monitoramento Logístico | Squad Cyberkayzen")
st.subheader("Análise Estratégica de Performance e Atrasos de Entregas")
st.markdown("---")

# Barra Lateral para Filtros
st.sidebar.header("Filtros Dinâmicos")
regiao_selecionada = st.sidebar.multiselect("Selecione a Região:", options=df_original['Regiao'].unique(), default=df_original['Regiao'].unique())
transp_selecionada = st.sidebar.multiselect("Selecione a Transportadora:", options=df_original['Transportadora'].unique(), default=df_original['Transportadora'].unique())

# Filtrando o dataframe
df_filtrado = df_original[
    (df_original['Regiao'].isin(regiao_selecionada)) & 
    (df_original['Transportadora'].isin(transp_selecionada))
]

# ==============================================================================
# CARD DE INDICADORES (KPIs Principais)
# ==============================================================================
total_entregas = len(df_filtrado)
total_atrasos = len(df_filtrado[df_filtrado['Status'] == 'Atrasado'])
taxa_atraso = (total_atrasos / total_entregas * 100) if total_entregas > 0 else 0
media_atraso = df_filtrado[df_filtrado['Dias_Atraso'] > 0]['Dias_Atraso'].mean()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Entregas", f"{total_entregas}")
with col2:
    st.metric("Entregas em Atraso 🚨", f"{total_atrasos}")
with col3:
    st.metric("Taxa de Atraso (%)", f"{taxa_atraso:.1f}%", delta=f"{taxa_atraso-15:.1f}% vs Meta", delta_color="inverse")
with col4:
    st.metric("Tempo Médio de Atraso", f"{media_atraso:.1f} dias" if not np.isnan(media_atraso) else "0 dias")

st.markdown("---")

# ==============================================================================
# GRÁFICOS (Tendências e Comparações)
# ==============================================================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("📈 Tendência Operacional (Atrasos por Data Prometida)")
    # Agrupando por data para ver a tendência
    df_tendencia = df_filtrado[df_filtrado['Status'] == 'Atrasado'].groupby('Data_Prometida').size().reset_index(name='Qtd_Atrasos')
    fig_linha = px.line(df_tendencia, x='Data_Prometida', y='Qtd_Atrasos', title="Evolução do Volume de Atrasos", markers=True)
    st.plotly_chart(fig_linha, use_container_width=True)

with col_graf2:
    st.subheader("🚛 Comparação entre Transportadoras")
    df_transp = df_filtrado.groupby(['Transportadora', 'Status']).size().reset_index(name='Quantidade')
    fig_barra = px.bar(df_transp, x='Transportadora', y='Quantidade', color='Status', 
                       title="Status de Entrega por Parceiro", barmode="stack",
                       color_discrete_map={'No Prazo': '#2ecc71', 'Atrasado': '#e74c3c', 'Pendente no Prazo': '#f1c40f'})
    st.plotly_chart(fig_barra, use_container_width=True)

col_graf3, _ = st.columns([2, 2])
with col_graf3:
    st.subheader("🗺️ Análise por Região Crítica")
    df_regiao = df_filtrado[df_filtrado['Status'] == 'Atrasado'].groupby('Regiao').size().reset_index(name='Total_Atrasos')
    df_regiao = df_regiao.sort_values(by='Total_Atrasos', ascending=False)
    fig_regiao = px.bar(df_regiao, x='Total_Atrasos', y='Regiao', orientation='h', title="Gargalos por Região Geográfica", color='Total_Atrasos', color_continuous_scale='Reds')
    st.plotly_chart(fig_regiao, use_container_width=True)

st.markdown("---")

# ==============================================================================
# REQUISITO: PRIORIZAÇÃO VISUAL (Tabela Dinâmica / Alertas)
# ==============================================================================
st.subheader("🔥 Matriz de Priorização de Entregas Críticas")
st.markdown("Pedidos abaixo necessitam de intervenção imediata da equipe de atendimento/logística (Ordenado por Dias de Atraso).")

# Filtrando apenas os problemas reais (Atrasados), ordenados do maior para o menor atraso
df_critico = df_filtrado[df_filtrado['Status'] == 'Atrasado'].sort_values(by=['Dias_Atraso', 'Valor_Carga'], ascending=[False, False])

# Formatando as colunas de data para exibição bonita
df_critico_exibicao = df_critico.copy()
df_critico_exibicao['Data_Prometida'] = df_critico_exibicao['Data_Prometida'].dt.strftime('%d/%m/%Y')
df_critico_exibicao['Data_Efetiva'] = df_critico_exibicao['Data_Efetiva'].dt.strftime('%d/%m/%Y').fillna("Em Trânsito")

# Aplicando destaque visual na tabela do Streamlit usando Pandas Styler
def destacar_criticos(val):
    if val > 7:
        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'  # Vermelho para > 7 dias
    elif val > 3:
        return 'background-color: #ffe6cc; color: #cc6600;'  # Laranja para atraso intermediário
    return 'background-color: #fff5cc; color: #997300;'

st.dataframe(
    df_critico_exibicao[['ID_Pedido', 'Regiao', 'Transportadora', 'Data_Prometida', 'Dias_Atraso', 'Valor_Carga']].style.applymap(destacar_criticos, subset=['Dias_Atraso']),
    use_container_width=True
)