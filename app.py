import streamlit as st
import pandas as pd
import plotly.express as px
import re
import os
import glob

# Configuração da página para tela inteira
st.set_page_config(layout="wide", page_title="Dashboard Unioeste - Nivelamento", page_icon="📊")

# Função auxiliar para renderizar gráficos sem alertas de versão
def exibir_grafico(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# 1. CARREGAMENTO AUTOMÁTICO DOS DOIS ARQUIVOS EXCEL
# -------------------------------------------------------------
@st.cache_data
def carregar_dados():
    # Busca da planilha de docentes
    arq_doc = None
    candidatos_doc = [
        'QUESTIONÁRIO DOS DOCENTES – LEVANTAMENTO DE CARÊNCIAS DOS ALUNOS INGRESSANTES (respostas)_2.xlsx',
        'QUESTIONÁRIO DOS DOCENTES – LEVANTAMENTO DE CARÊNCIAS DOS ALUNOS INGRESSANTES (respostas).xlsx'
    ]
    for c in candidatos_doc:
        if os.path.exists(c):
            arq_doc = c
            break
    if not arq_doc:
        g = glob.glob("*DOCENTES*.xlsx")
        if g: arq_doc = g[0]
        else: raise FileNotFoundError("Planilha de DOCENTES não encontrada na pasta.")

    # Busca da planilha de estudantes
    arq_est = None
    candidatos_est = [
        'QUESTIONÁRIO PARA ESTUDANTES – MAPEAMENTO DE DIFICULDADES NO INGRESSO (respostas)_2.xlsx',
        'QUESTIONÁRIO PARA ESTUDANTES – MAPEAMENTO DE DIFICULDADES NO INGRESSO (respostas).xlsx'
    ]
    for c in candidatos_est:
        if os.path.exists(c):
            arq_est = c
            break
    if not arq_est:
        g = glob.glob("*ESTUDANTES*.xlsx")
        if g: arq_est = g[0]
        else: raise FileNotFoundError("Planilha de ESTUDANTES não encontrada na pasta.")

    df_doc = pd.read_excel(arq_doc)
    df_est = pd.read_excel(arq_est)

    # Padroniza o nome da coluna Campus em ambas as bases
    col_campus_doc = df_doc.columns[3]
    df_doc.rename(columns={col_campus_doc: 'Campus'}, inplace=True)

    col_campus_est = df_est.columns[4]
    df_est.rename(columns={col_campus_est: 'Campus'}, inplace=True)

    return df_doc, df_est, arq_doc, arq_est

try:
    df_doc_raw, df_est_raw, nome_doc, nome_est = carregar_dados()
except Exception as e:
    st.error(f"Erro ao localizar/carregar as planilhas: {e}")
    st.stop()

# -------------------------------------------------------------
# 2. FILTRO GLOBAL POR CAMPUS NA BARRA LATERAL (SIDEBAR)
# -------------------------------------------------------------
st.sidebar.title("🔍 Filtros Globais")
campi_disponiveis = sorted(list(set(df_doc_raw['Campus'].dropna().astype(str).tolist() + df_est_raw['Campus'].dropna().astype(str).tolist())))
lista_campi = ["Todos os Campi"] + campi_disponiveis

campus_selecionado = st.sidebar.selectbox("Selecione o Campus:", lista_campi)

# Aplica o filtro em ambas as tabelas
if campus_selecionado != "Todos os Campi":
    df_doc = df_doc_raw[df_doc_raw['Campus'] == campus_selecionado]
    df_est = df_est_raw[df_est_raw['Campus'] == campus_selecionado]
else:
    df_doc = df_doc_raw
    df_est = df_est_raw

st.sidebar.divider()
st.sidebar.metric("Docentes Respondentes", f"{len(df_doc)} profs")
st.sidebar.metric("Estudantes Respondentes", f"{len(df_est)} alunos")

# Funções utilitárias de gráficos
def plotar_escala(df_dados, col_nome, titulo, ordem, cores):
    dados = df_dados[col_nome].value_counts().reindex(ordem, fill_value=0).reset_index()
    dados.columns = ['Nível', 'Respostas']
    fig = px.bar(
        dados, x='Respostas', y='Nível', orientation='h', color='Nível',
        color_discrete_map=cores, title=titulo, text='Respostas'
    )
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=35, b=10), height=250)
    fig.update_traces(textposition='outside')
    return fig

def plotar_multipla_escolha(df_dados, col_nome, titulo, cor_seq='Blues'):
    respostas = []
    for val in df_dados[col_nome].dropna():
        itens = re.split(r',\s*(?![^()]*\))', str(val))
        respostas.extend([item.strip() for item in itens if item.strip()])
    
    if not respostas:
        st.info("Nenhuma resposta registrada para este campus nesta questão.")
        return
        
    contagem = pd.Series(respostas).value_counts().reset_index()
    contagem.columns = ['Opção', 'Respostas']
    
    fig = px.bar(
        contagem, x='Respostas', y='Opção', orientation='h', color='Respostas',
        color_continuous_scale=cor_seq, title=titulo, text='Respostas'
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=35, b=10), height=max(280, len(contagem)*32))
    fig.update_traces(textposition='outside')
    exibir_grafico(fig)

# -------------------------------------------------------------
# 3. ABAS PRINCIPAIS DO NAVEGADOR (TABS)
# -------------------------------------------------------------
tab_docentes, tab_estudantes = st.tabs([
    "👨‍🏫 Questionário dos Docentes",
    "🎓 Questionário dos Estudantes"
])

# =============================================================
# ABA 1: QUESTIONÁRIO DOS DOCENTES (COLUNAS AB A AY)
# =============================================================
with tab_docentes:
    st.header(f"Carências dos Ingressantes sob a ótica Docente ({campus_selecionado})")
    st.caption(f"Arquivo: `{nome_doc}` | Total de respostas: {len(df_doc)}")

    ordem_doc = ['1 – Sem carência', '2 – Baixa carência', '3 – Média carência', '4 – Alta carência', '5 – Carência crítica']
    cores_doc = {
        '1 – Sem carência': '#2ecc71', '2 – Baixa carência': '#a8e6cf',
        '3 – Média carência': '#ffd3b6', '4 – Alta carência': '#ff8b94', '5 – Carência crítica': '#d9534f'
    }

    # Seção 1: Língua Portuguesa
    st.subheader("1. Língua Portuguesa e Comunicação")
    c1, c2 = st.columns(2)
    with c1:
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[27], "AB. Compreensão e interpretação de textos", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[29], "AD. Domínio da norma culta", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[31], "AF. Habilidade para fazer anotações/registros", ordem_doc, cores_doc))
    with c2:
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[28], "AC. Produção de textos (coerência, coesão)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[30], "AE. Capacidade de síntese e resumo", ordem_doc, cores_doc))

    st.divider()

    # Seção 2: Matemática
    st.subheader("2. Raciocínio Lógico-Matemático")
    c3, c4 = st.columns(2)
    with c3:
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[32], "AG. Operações básicas (aritmética, frações, %)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[34], "AI. Noções de álgebra (equações 1º e 2º grau)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[36], "AK. Leitura de gráficos e tabelas", ordem_doc, cores_doc))
    with c4:
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[33], "AH. Raciocínio proporcional (regra de três)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[35], "AJ. Noções de geometria (áreas, perímetros)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[37], "AL. Raciocínio lógico e resolução de problemas", ordem_doc, cores_doc))

    st.divider()

    # Seção 3: Informática
    st.subheader("3. Informática e Tecnologias Digitais")
    c5, c6 = st.columns(2)
    with c5:
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[38], "AM. Editores de texto (Word, Docs)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[40], "AO. Ferramentas de apresentação (PowerPoint)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[42], "AQ. E-mail institucional e AVAs (Moodle, Teams)", ordem_doc, cores_doc))
    with c6:
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[39], "AN. Planilhas eletrônicas (Excel, Calc)", ordem_doc, cores_doc))
        exibir_grafico(plotar_escala(df_doc, df_doc.columns[41], "AP. Pesquisa em bases acadêmicas (Capes, SciELO)", ordem_doc, cores_doc))

    st.divider()

    # Seção 4: Conteúdos por Área
    st.subheader("4. Conteúdos Específicos por Área")
    plotar_multipla_escolha(df_doc, df_doc.columns[43], "AR. Área de Humanas")
    plotar_multipla_escolha(df_doc, df_doc.columns[44], "AS. Área de Biológicas e Saúde")
    plotar_multipla_escolha(df_doc, df_doc.columns[45], "AT. Área de Exatas e Engenharias")
    plotar_multipla_escolha(df_doc, df_doc.columns[46], "AU. Área de Licenciaturas e Pedagogia")

    st.divider()

    # Seção 5: Habilidades Transversais e Anotações
    st.subheader("5. Habilidades Transversais e Anotações Livres")
    plotar_multipla_escolha(df_doc, df_doc.columns[47], "AV. Habilidades transversais mais deficitárias")

    st.write("---")
    respostas_aw = df_doc[df_doc.columns[48]].dropna().tolist()
    st.write(f"**AW. Anotações Dissertativas dos Docentes ({len(respostas_aw)} respostas):**")
    with st.expander("🔍 Clique aqui para ler as sugestões abertas dos professores"):
        termo = st.text_input("Filtrar sugestões por palavra-chave:", key="busca_doc")
        if termo:
            respostas_aw = [r for r in respostas_aw if termo.lower() in str(r).lower()]
        for idx, txt in enumerate(respostas_aw, 1):
            st.markdown(f"**{idx}.** {txt}")

    st.divider()

    # Seção 6: Proposta de Nivelamento
    st.subheader("6. Proposta de Nivelamento - Visão Docente")
    c7, c8 = st.columns(2)
    with c7:
        d_ax = df_doc[df_doc.columns[49]].value_counts().reset_index()
        d_ax.columns = ['Carga Horária', 'Votos']
        fig_ax = px.bar(d_ax, x='Votos', y='Carga Horária', orientation='h', color='Carga Horária', title="AX. Carga Horária Mínima Necessária", text='Votos')
        fig_ax.update_traces(textposition='outside')
        exibir_grafico(fig_ax)
    with c8:
        d_ay = df_doc[df_doc.columns[50]].value_counts().reset_index()
        d_ay.columns = ['Formato', 'Votos']
        fig_ay = px.pie(d_ay, values='Votos', names='Formato', title="AY. Formato Mais Adequado", hole=0.35)
        exibir_grafico(fig_ay)


# =============================================================
# ABA 2: QUESTIONÁRIO DOS ESTUDANTES (COLUNAS K A AF)
# =============================================================
with tab_estudantes:
    st.header(f"Dificuldades no Ingresso sob a ótica dos Estudantes ({campus_selecionado})")
    st.caption(f"Arquivo: `{nome_est}` | Total de respostas: {len(df_est)}")

    ordem_est = ['1 – Nenhuma dificuldade', '2 – Pouca dificuldade', '3 – Média dificuldade', '4 – Alta dificuldade', '5 – Dificuldade extrema']
    cores_est = {
        '1 – Nenhuma dificuldade': '#2ecc71', '2 – Pouca dificuldade': '#a8e6cf',
        '3 – Média dificuldade': '#ffd3b6', '4 – Alta dificuldade': '#ff8b94', '5 – Dificuldade extrema': '#d9534f'
    }

    # Seção 1: Choque de Realidade e Maior Dificuldade
    st.subheader("1. Transição para o Ensino Superior")
    ce1, ce2 = st.columns([1, 2])
    with ce1:
        # Coluna K: Escala de 0 a 10
        choque = df_est[df_est.columns[10]].value_counts().sort_index().reset_index()
        choque.columns = ['Nota', 'Alunos']
        fig_k = px.bar(choque, x='Nota', y='Alunos', title="K. Choque de Realidade (0 a 10)", text='Alunos', color='Nota', color_continuous_scale='Purples')
        fig_k.update_traces(textposition='outside')
        exibir_grafico(fig_k)
    with ce2:
        # Coluna L: Maior dificuldade (Resposta Única com Campo Aberto)
        col_l = df_est.columns[11]
        s_l = df_est[col_l].dropna()
        
        if s_l.empty:
            st.info("Nenhuma resposta registrada para este campus nesta questão.")
        else:
            opcoes_padrao_l = [
                'Conciliar a faculdade com trabalho/outras responsabilidades',
                'Fazer as leituras obrigatórias com profundidade',
                'Acompanhar o ritmo dos professores nas aulas',
                'Gerenciar a ansiedade e o medo de reprovar',
                'Entender a linguagem acadêmica (termos técnicos, jargões)',
                'Escrever trabalhos e provas dissertativas',
                'Fazer amizades e se enturmar',
                'Usar as ferramentas digitais (Google Sala de Aula, bibliotecas virtuais)'
                'Resolver exercícios e problemas práticos',
            ]
            
            # Identifica respostas personalizadas (digitadas no campo "Outro")
            respostas_custom = s_l[~s_l.isin(opcoes_padrao_l)].tolist()
            
            # Agrupa as personalizadas em "Outros" para não poluir o gráfico
            s_l_agrupada = s_l.apply(lambda x: x if x in opcoes_padrao_l else 'Outros (respostas dissertativas)')
            contagem_l = s_l_agrupada.value_counts().reset_index()
            contagem_l.columns = ['Dificuldade', 'Alunos']
            
            fig_l = px.bar(
                contagem_l, 
                x='Alunos', 
                y='Dificuldade', 
                orientation='h', 
                color='Alunos',
                color_continuous_scale='Teal', 
                title="L. Maior dificuldade enfrentada no início", 
                text='Alunos'
            )
            fig_l.update_layout(
                yaxis=dict(autorange="reversed"), 
                margin=dict(l=10, r=10, t=35, b=10), 
                height=340
            )
            fig_l.update_traces(textposition='outside')
            exibir_grafico(fig_l)
            
            # Expansor com os parágrafos completos escritos pelos estudantes
            if respostas_custom:
                with st.expander(f"📝 Ver respostas dissertativas de 'Outros' ({len(respostas_custom)} relatos)"):
                    for idx_c, r_text in enumerate(respostas_custom, 1):
                        st.markdown(f"**{idx_c}.** {r_text}")
    st.divider()

    # Seção 2: Leitura, Escrita e Comunicação (M a Q)
    st.subheader("2. Leitura, Escrita e Comunicação")
    cm1, cm2 = st.columns(2)
    with cm1:
        exibir_grafico(plotar_escala(df_est, df_est.columns[12], "M. Interpretar textos longos e complexos", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[14], "O. Fazer bom resumo ou fichamento", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[16], "Q. Entender o que o professor espera em discursivas", ordem_est, cores_est))
    with cm2:
        exibir_grafico(plotar_escala(df_est, df_est.columns[13], "N. Escrever com clareza e sem erros", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[15], "P. Interpretar gráficos e tabelas", ordem_est, cores_est))

    st.divider()

    # Seção 3: Matemática e Raciocínio Lógico (R a U)
    st.subheader("3. Matemática e Raciocínio Lógico")
    cr1, cr2 = st.columns(2)
    with cr1:
        exibir_grafico(plotar_escala(df_est, df_est.columns[17], "R. Operações básicas (frações, %, regra de 3)", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[19], "T. Noções de probabilidade e estatística", ordem_est, cores_est))
    with cr2:
        exibir_grafico(plotar_escala(df_est, df_est.columns[18], "S. Raciocínio lógico para problemas práticos", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[20], "U. Equações e funções", ordem_est, cores_est))

    st.divider()

    # Seção 4: Informática e Tecnologia (V a Y)
    st.subheader("4. Informática e Tecnologia")
    ci1, ci2 = st.columns(2)
    with ci1:
        exibir_grafico(plotar_escala(df_est, df_est.columns[21], "V. Formatar trabalhos (Word/ABNT)", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[23], "X. Pesquisa em bases científicas (SciELO, Capes)", ordem_est, cores_est))
    with ci2:
        exibir_grafico(plotar_escala(df_est, df_est.columns[22], "W. Planilhas no Excel/Calc", ordem_est, cores_est))
        exibir_grafico(plotar_escala(df_est, df_est.columns[24], "Y. E-mail institucional e sistemas acadêmicos", ordem_est, cores_est))

    st.divider()

    # Seção 5: Conteúdos por Área e Habilidades Não Técnicas (Z a AC)
    st.subheader("5. Conteúdos por Área e Habilidades Pessoais")
    plotar_multipla_escolha(df_est, df_est.columns[25], "Z. Conteúdos que faltaram - Humanas e Sociais Aplicadas", cor_seq='Sunset')
    plotar_multipla_escolha(df_est, df_est.columns[26], "AA. Conteúdos que faltaram - Saúde e Biológicas", cor_seq='Sunset')
    plotar_multipla_escolha(df_est, df_est.columns[27], "AB. Conteúdos que faltaram - Exatas e Engenharias", cor_seq='Sunset')
    plotar_multipla_escolha(df_est, df_est.columns[28], "AC. Habilidades NÃO técnicas mais sentidas pelos alunos", cor_seq='Oranges')

    st.divider()

    # Seção 6: Proposta de Nivelamento (AD a AF)
    st.subheader("6. Formato Ideal de Nivelamento - Visão Discente")
    ca1, ca2, ca3 = st.columns(3)
    with ca1:
        d_ad = df_est[df_est.columns[29]].value_counts().reset_index()
        d_ad.columns = ['Formato', 'Votos']
        fig_ad = px.pie(d_ad, values='Votos', names='Formato', title="AD. Formato Mais Proveitoso", hole=0.35)
        exibir_grafico(fig_ad)
    with ca2:
        d_ae = df_est[df_est.columns[30]].value_counts().reset_index()
        d_ae.columns = ['Carga Horária', 'Votos']
        fig_ae = px.bar(d_ae, x='Votos', y='Carga Horária', orientation='h', color='Carga Horária', title="AE. Carga Horária Suportável", text='Votos')
        fig_ae.update_traces(textposition='outside')
        exibir_grafico(fig_ae)
    with ca3:
        d_af = df_est[df_est.columns[31]].value_counts().reset_index()
        d_af.columns = ['Horário', 'Votos']
        fig_af = px.pie(d_af, values='Votos', names='Horário', title="AF. Melhor Horário para as Aulas", hole=0.35)
        exibir_grafico(fig_af)