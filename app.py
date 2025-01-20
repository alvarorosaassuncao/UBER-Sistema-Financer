import streamlit as st
import pandas as pd
from datetime import datetime
import io
import cv2
import numpy as np
import base64  # Importe o módulo base64

# Configuração da página
st.set_page_config(
    page_title="UBER Finacer - Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

# Função para carregar uma imagem de fundo com OpenCV
def add_bg_from_local(image_file):
    imagem = cv2.imread(image_file)
    imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)  # Converte de BGR para RGB
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{base64.b64encode(cv2.imencode('.png', imagem)[1]).decode()});
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Adicionar imagem de fundo (substitua 'background.jpg' pelo caminho da sua imagem)
add_bg_from_local('background.jpg')

# Inicializar o estado da sessão
if 'rides' not in st.session_state:
    st.session_state.rides = pd.DataFrame(columns=['data', 'valor', 'quilometragem', 'tipo', 'categoria', 'descricao'])

# Barra lateral para navegação
st.sidebar.title("UBER Finacer - Controle Financeiro")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Registrar", "Relatórios", "Dados"]
)

# Estilos personalizados
st.markdown("""
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stMetric {
        padding: 25px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
    }
    .metric-receita {
        background-color: #4CAF50; /* Verde */
    }
    .metric-despesa {
        background-color: #FF4B4B; /* Vermelho */
    }
    .metric-saldo {
        background-color: #1E90FF; /* Azul */
    }
    .metric-title {
        font-size: 20px;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 28px;
        margin-top: 10px;
    }
    .stDataFrame {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para adicionar uma nova entrada
def add_entry(data, valor, quilometragem, tipo, categoria, descricao):
    new_entry = pd.DataFrame({
        'data': [data],
        'valor': [valor],
        'quilometragem': [quilometragem],
        'tipo': [tipo],
        'categoria': [categoria],
        'descricao': [descricao]
    })
    st.session_state.rides = pd.concat([st.session_state.rides, new_entry], ignore_index=True)

# Função para exportar dados
def export_data(format='csv'):
    if format == 'csv':
        return st.session_state.rides.to_csv(index=False)
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.rides.to_excel(writer, index=False)
        return output.getvalue()

# Página: Dashboard
if page == "Dashboard":
    st.title("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Métricas
    receitas = st.session_state.rides[st.session_state.rides['tipo'] == 'entrada']['valor'].sum()
    despesas = st.session_state.rides[st.session_state.rides['tipo'] == 'saida']['valor'].sum()
    saldo = receitas - despesas
    
    with col1:
        st.markdown(
            f"""
            <div class="stMetric metric-receita">
                <div class="metric-title">Receitas</div>
                <div class="metric-value">R$ {receitas:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div class="stMetric metric-despesa">
                <div class="metric-title">Despesas</div>
                <div class="metric-value">R$ {despesas:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div class="stMetric metric-saldo">
                <div class="metric-title">Saldo</div>
                <div class="metric-value">R$ {saldo:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Gráficos
    if not st.session_state.rides.empty:
        # Verifica se há entradas registradas
        entradas = st.session_state.rides[st.session_state.rides['tipo'] == 'entrada']
        if not entradas.empty:
            # Garante que a coluna 'data' esteja no formato de data
            entradas['data'] = pd.to_datetime(entradas['data'])
            
            # Formata as datas para o formato dd/mm/yyyy
            entradas['data_formatada'] = entradas['data'].dt.strftime('%d/%m/%Y')
            
            # Agrupa os dados por data e soma os valores
            dados_agrupados = entradas.groupby('data_formatada')['valor'].sum().reset_index()
            
            # Gráfico de barras temporal
            fig_bar = px.bar(
                dados_agrupados,
                x='data_formatada',
                y='valor',
                title='Ganhos ao Longo do Tempo',
                labels={'data_formatada': 'Data', 'valor': 'Valor (R$)'},
                text='valor'
            )
            
            # Formatação do eixo X (datas)
            fig_bar.update_xaxes(
                title_text='Data'
            )
            
            # Formatação do eixo Y (valores)
            fig_bar.update_yaxes(
                title_text='Valor (R$)'
            )
            
            # Melhora a legibilidade dos rótulos
            fig_bar.update_traces(
                textposition='outside',  # Posiciona os valores acima das barras
                texttemplate='R$ %{y:.2f}'  # Formato dos valores
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Nenhuma entrada registrada para exibir o gráfico de ganhos.")
        
        # Gráfico de pizza para despesas
        despesas_cat = st.session_state.rides[st.session_state.rides['tipo'] == 'saida'].groupby('categoria')['valor'].sum()
        if not despesas_cat.empty:
            fig_pie = px.pie(
                values=despesas_cat.values,
                names=despesas_cat.index,
                title='Distribuição de Despesas'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Nenhuma despesa registrada para exibir o gráfico de distribuição.")
    else:
        st.info("Adicione dados para começar a análise.")

# Página: Registrar
elif page == "Registrar":
    st.title("Registrar Movimento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data = st.date_input("Data", datetime.now())
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        quilometragem = st.number_input("Quilometragem (km)", min_value=0.0, step=0.1)
    
    with col2:
        tipo = st.selectbox("Tipo", ["entrada", "saida"])
        categoria = st.selectbox(
            "Categoria",
            ["Corrida", "Combustível", "Manutenção", "Alimentação", "Outros"] if tipo == "saida" else ["Uber", "Outros"]
        )
        descricao = st.text_area("Descrição")
    
    if st.button("Registrar"):
        add_entry(data, valor, quilometragem, tipo, categoria, descricao)
        st.success("Registro adicionado com sucesso!")

# Página: Relatórios
elif page == "Relatórios":
    st.title("Relatórios")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data Inicial")
    with col2:
        end_date = st.date_input("Data Final")
    
    # Botões de exportação
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Exportar CSV"):
            csv = export_data('csv')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="finacer_report.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Exportar Excel"):
            excel = export_data('excel')
            st.download_button(
                label="Download Excel",
                data=excel,
                file_name="finacer_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Página: Dados
elif page == "Dados":
    st.title("Visualização de Dados")
    
    # Tabela editável
    if not st.session_state.rides.empty:
        st.dataframe(st.session_state.rides, use_container_width=True)
        
        # Opção para editar ou excluir linhas
        st.subheader("Editar ou Excluir Registros")
        row_to_edit = st.number_input("Número da linha para editar/excluir", min_value=0, max_value=len(st.session_state.rides)-1, step=1)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Editar Linha"):
                st.session_state.edit_mode = True
                st.session_state.row_to_edit = row_to_edit
        
        with col2:
            if st.button("Excluir Linha"):
                st.session_state.rides = st.session_state.rides.drop(index=row_to_edit).reset_index(drop=True)
                st.success("Linha excluída com sucesso!")
        
        if st.session_state.get('edit_mode', False):
            st.subheader("Editar Registro")
            edited_data = st.date_input("Data", value=pd.to_datetime(st.session_state.rides.loc[row_to_edit, 'data']))
            edited_valor = st.number_input("Valor (R$)", value=st.session_state.rides.loc[row_to_edit, 'valor'])
            edited_quilometragem = st.number_input("Quilometragem (km)", value=st.session_state.rides.loc[row_to_edit, 'quilometragem'])
            edited_tipo = st.selectbox("Tipo", ["entrada", "saida"], index=0 if st.session_state.rides.loc[row_to_edit, 'tipo'] == "entrada" else 1)
            edited_categoria = st.selectbox(
                "Categoria",
                ["Corrida", "Combustível", "Manutenção", "Alimentação", "Outros"] if edited_tipo == "saida" else ["Uber", "Outros"],
                index=0 if st.session_state.rides.loc[row_to_edit, 'categoria'] == "Uber" else 1
            )
            edited_descricao = st.text_area("Descrição", value=st.session_state.rides.loc[row_to_edit, 'descricao'])
            
            if st.button("Salvar Edição"):
                st.session_state.rides.loc[row_to_edit] = [edited_data, edited_valor, edited_quilometragem, edited_tipo, edited_categoria, edited_descricao]
                st.session_state.edit_mode = False
                st.success("Registro editado com sucesso!")
    else:
        st.info("Nenhum dado registrado para exibir.")
