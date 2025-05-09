import streamlit as st
import pandas as pd
import altair as alt
import yaml
from yaml.loader import SafeLoader

# ✅ Configurando a página (DEVE SER A PRIMEIRA LINHA)
st.set_page_config(page_title="Dashboard", layout="wide")

# Verificando se o arquivo existe e está correto
try:
    with open('users.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Arquivo 'users.yaml' não encontrado.")
except yaml.YAMLError:
    st.error("Erro ao carregar o arquivo 'users.yaml'. Verifique o formato.")

# Garantindo o estado inicial da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""

# ✅ Função para exibir gráfico de barras interativo por Marca (com Altair)
def plot_interactive_chart(df):
    st.subheader("📊 Itens Comprados por Marca")

    marcas = df['Marca'].unique().tolist()
    selected_marca = st.multiselect("Selecione a Marca:", marcas, default=marcas)

    df_filtered = df[df['Marca'].isin(selected_marca)]
    
    chart = alt.Chart(df_filtered).mark_bar().encode(
        x=alt.X('Quantidade:Q', title='Quantidade de Itens'),
        y=alt.Y('Marca:N', sort='-x', title='Marca'),
        color='Marca',
        tooltip=['Marca', 'Quantidade']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    
    return df_filtered

# ✅ Função para exibir a dashboard
def show_dashboard():
    st.header("Painel Dorel")

    try:
        df = pd.read_csv("produtos1.csv", sep=';', engine='python')
        if len(df.columns) == 1:
            df = pd.read_csv("produtos1.csv", sep=',')

        st.write("✅ Dados carregados com sucesso!")

        df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0).astype(int)
        df['Valor'] = (
            df['Valor']
            .astype(str)
            .str.replace("R\$", "", regex=True)
            .str.replace(" ", "")
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0).astype(float)

        if st.session_state['role'] == 'admin':
            st.subheader("Admin Dashboard - Visualizando todos os dados")

            # ✅ Gráfico Interativo (por Marca)
            df_filtered = plot_interactive_chart(df)

            # ✅ Recalculando os KPIs com base na seleção
            total_quantidade = df_filtered['Quantidade'].sum()
            total_valor = (df_filtered['Valor'] * df_filtered['Quantidade']).sum()

            # ✅ KPIs ACIMA DO GRÁFICO
            st.subheader("📊 Indicadores Gerais")
            col1, col2 = st.columns(2)
            col1.metric("Total de Itens Comprados", f"{total_quantidade}")
            col2.metric("Valor Total", f"R$ {total_valor:,.2f}")

            st.subheader("📋 Histórico de Pedidos")
            df_display = df_filtered.copy()
            df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(df_display)

        else:
            cliente = st.session_state['username']
            df_cliente = df[df['Cliente'] == cliente]
            df_cliente = df_cliente.drop(columns=['Cliente'], errors='ignore')

            # ✅ Gráfico Interativo (por Marca)
            df_filtered = plot_interactive_chart(df_cliente)

            # ✅ Recalculando os KPIs com base na seleção
            total_quantidade = df_filtered['Quantidade'].sum()
            total_valor = (df_filtered['Valor'] * df_filtered['Quantidade']).sum()

            st.subheader(f"Dashboard do Cliente: {cliente}")

            # ✅ KPIs ACIMA DO GRÁFICO
            st.subheader("📊 Indicadores Gerais")
            col1, col2 = st.columns(2)
            col1.metric("Total de Itens Comprados", f"{total_quantidade}")
            col2.metric("Valor Total", f"R$ {total_valor:,.2f}")

            st.subheader("📋 Histórico de Pedidos")
            df_cliente_display = df_filtered.copy()
            df_cliente_display['Valor'] = df_cliente_display['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(df_cliente_display)

    except FileNotFoundError:
        st.error("Arquivo CSV não encontrado. Verifique o caminho.")

# ✅ Controle de Login e Dashboard
if st.session_state.authenticated:
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.clear()
        st.success("Você saiu com sucesso. Recarregue a página para voltar ao login.")
        st.stop()

    show_dashboard()

else:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if username in config['credentials']['usernames']:
            user_data = config['credentials']['usernames'][username]
            stored_password = user_data['password']

            if password == stored_password:
                st.session_state.username = username
                st.session_state.authenticated = True
                st.session_state.role = user_data['role']
                st.success(f"Welcome, {user_data['name']}!")
            else:
                st.error("Incorrect username or password.")
        else:
            st.error("Username not found.")

    if st.session_state.authenticated:
        show_dashboard()
