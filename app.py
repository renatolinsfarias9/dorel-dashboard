import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

# ✅ Função para exibir gráfico de barras horizontal por Marca
def plot_bar_chart(df_plot):
    st.subheader("📊 Itens Comprados por Marca")
    marcas = df_plot.groupby('Marca')['Quantidade'].sum().sort_values()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(marcas.index, marcas.values, color="#4E79A7")

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.2, bar.get_y() + bar.get_height() / 2,
                f'{int(width)}', va='center', fontsize=9)

    ax.set_xlabel("Quantidade")
    ax.set_ylabel("Marca")
    ax.set_title("Quantidade de Itens Comprados por Marca")
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    st.pyplot(fig)

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
            total_quantidade = df['Quantidade'].sum()
            total_valor = (df['Valor'] * df['Quantidade']).sum()

            col1, col2 = st.columns(2)
            col1.metric("Total de Itens Comprados", f"{total_quantidade}")
            col2.metric("Valor Total", f"R$ {total_valor:,.2f}")

            # ✅ Gráfico Admin (por Marca)
            plot_bar_chart(df)

            st.subheader("📋 Histórico de Pedidos")
            df_display = df.copy()
            df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(df_display)

        else:
            cliente = st.session_state['username']
            df_cliente = df[df['Cliente'] == cliente]
            df_cliente = df_cliente.drop(columns=['Cliente'], errors='ignore')

            total_quantidade = df_cliente['Quantidade'].sum()
            total_valor = (df_cliente['Valor'] * df_cliente['Quantidade']).sum()

            st.subheader(f"Dashboard do Cliente: {cliente}")

            col1, col2 = st.columns(2)
            col1.metric("Total de Itens Comprados", f"{total_quantidade}")
            col2.metric("Valor Total", f"R$ {total_valor:,.2f}")

            # ✅ Gráfico Cliente (por Marca)
            plot_bar_chart(df_cliente)

            st.subheader("📋 Histórico de Pedidos")
            df_cliente_display = df_cliente.copy()
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
        st.stop()  # Impede a exibição da dashboard após o logout

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
