import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import sqlite3

# =================================================
# CONFIGURAÇÃO INICIAL
# =================================================
st.set_page_config(
    page_title="Ranking de Recompensas - Manutenção",
    layout="wide"
)

VALOR_PONTO = 1.60

# =================================================
# CONEXÃO COM BANCO
# =================================================
def get_conn():
    return sqlite3.connect("ranking.db", check_same_thread=False)

conn = get_conn()
cursor = conn.cursor()

# =====================================
# MIGRAÇÃO: ADICIONAR COLUNA 'ativo'
# =====================================
try:
    cursor.execute("ALTER TABLE colaboradores ADD COLUMN ativo INTEGER DEFAULT 1")
    conn.commit()
except sqlite3.OperationalError:
    pass

# =================================================
# CRIAÇÃO DAS TABELAS
# =================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS colaboradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE,
    pontos_iniciais INTEGER,
    ativo INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colaborador_id INTEGER,
    pontos INTEGER,
    descricao TEXT,
    data DATETIME
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tipos_penalidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT UNIQUE NOT NULL,
    valor INTEGER NOT NULL
)
""")
conn.commit()

# =================================================
# PENALIDADES PADRÃO
# =================================================
penalidades_iniciais = [
    ("Deixar de preencher relatório técnico da manutenção", -3),
    ("Deixar ferramenta ou item dentro do veículo após serviço", -3),
    ("Falta de atualização no sistema de controle de manutenção", -3),
    ("Falta de alinhamento com gestor sobre prioridades de serviço", -3),
    ("Executar manutenção em veículo errado / item incorreto", -15),
    ("Falta de comunicação com gestor sobre problemas", -15),
    ("Desorganização do ambiente de trabalho", -5),
    ("Falta de cuidado com ferramentas/equipamentos", -5),
    ("Não registrar o encerramento da O.S.", -5),
    ("Execução de manutenção sem checklist de inspeção", -5),
    ("Não comunicar defeito identificado em inspeção", -5),
    ("Falta na organização e devolução de peças substituídas", -5),
    ("Descarte incorreto de resíduos (óleo, filtros, peças)", -5),
    ("Comportamento inadequado ou desrespeito", -10),
    ("Execução de manutenção sem registro em O.S.", -10),
    ("Não seguir o plano de manutenção preventiva", -10),
    ("Instalação de peça fora de especificação", -10),
    ("Não cumprir prazo estabelecido em O.S.", -10),
    ("Uso incorreto de ferramenta ou equipamento", -10),
    ("Execução incorreta que gera retrabalho", -15),
    ("Utilizar peça ou material sem autorização", -15),
    ("Falta de inspeção antes da liberação do veículo", -15),
]

for desc, valor in penalidades_iniciais:
    cursor.execute("""
        INSERT OR IGNORE INTO tipos_penalidade (descricao, valor)
        VALUES (?, ?)
    """, (desc, valor))
conn.commit()

# =================================================
# INSERÇÃO INICIAL DE COLABORADORES
# =================================================
iniciais = ["André Omena", "Junior", "Rafael Dantas", "Tiago Silva"]
for nome in iniciais:
    cursor.execute("""
        INSERT OR IGNORE INTO colaboradores (nome, pontos_iniciais, ativo)
        VALUES (?, ?, 1)
    """, (nome, 100))
conn.commit()

# =================================================
# CSS MELHORADO (layout em colunas + design refinado)
# =================================================
st.markdown("""
<style>
body {
    background-color: #f8fafc;
}
.main-header {
    background: linear-gradient(135deg, #1e40af, #1d4ed8);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.section-title {
    font-size: 1.3rem;
    font-weight: 600;
    margin: 16px 0 12px 0;
    color: #1e3a8a;
    display: flex;
    align-items: center;
    gap: 8px;
}
.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
.kpi-box {
    background: white;
    padding: 16px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    border-top: 4px solid;
}
.kpi-box.pontos { border-color: #3b82f6; }
.kpi-box.recompensa { border-color: #10b981; }
.kpi-box.penalidades { border-color: #ef4444; }
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px;
    width: 100%;
}
.st-expander {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# HEADER
# =================================================
st.markdown('<div class="main-header">', unsafe_allow_html=True)
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.image("logo.png", width=120)
with col_titulo:
    st.markdown("### 🔧 **Ranking de Recompensas - Manutenção**")
    st.markdown("Gerenciamento de Pontos e Recompensas • **R$ 1,60 por ponto**")
st.markdown('</div>', unsafe_allow_html=True)

# =================================================
# COLUNAS PRINCIPAIS
# =================================================
col_left, col_right = st.columns([2, 1], gap="medium")

# =================================================
# COLUNA DA ESQUERDA: AÇÕES PRINCIPAIS
# =================================================
with col_left:

    # Seleção de colaborador
    df_colab = pd.read_sql("SELECT * FROM colaboradores WHERE ativo = 1", conn)
    st.markdown('<div class="section-title">👤 Selecionar Colaborador</div>', unsafe_allow_html=True)
    colaborador = st.selectbox(
        " ",
        ["Selecione"] + df_colab["nome"].tolist(),
        label_visibility="collapsed"
    )

    # Métricas (KPIs)
    if colaborador != "Selecione":
        query = """
        SELECT 
            c.pontos_iniciais + IFNULL(SUM(h.pontos),0) pontos,
            ABS(IFNULL(SUM(CASE WHEN h.pontos < 0 THEN h.pontos END),0)) penalidades
        FROM colaboradores c
        LEFT JOIN historico h ON h.colaborador_id = c.id
        WHERE c.nome = ?
        """
        pontos, total_penalidades = cursor.execute(query, (colaborador,)).fetchone()
        recompensa = max(pontos, 0) * VALOR_PONTO
    else:
        pontos = total_penalidades = recompensa = 0

    st.markdown('<div class="section-title">📊 Métricas Atuais</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box pontos"><h4>Pontos</h4><h2>{pontos}</h2></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box recompensa"><h4>Recompensa</h4><h2>R$ {recompensa:,.2f}</h2></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box penalidades"><h4>Penalidades</h4><h2>{total_penalidades}</h2></div>', unsafe_allow_html=True)

    # Aplicar Penalidade
    st.markdown('<div class="section-title">⚠️ Aplicar Penalidade</div>', unsafe_allow_html=True)
    df_penalidades = pd.read_sql("SELECT descricao, valor FROM tipos_penalidade ORDER BY valor, descricao", conn)
    penalidades = dict(zip(df_penalidades["descricao"], df_penalidades["valor"]))
    pen = st.selectbox(" ", ["Selecione"] + list(penalidades.keys()), label_visibility="collapsed")
    
    if st.button("Aplicar Penalidade"):
        if colaborador != "Selecione" and pen != "Selecione":
            colab_id = cursor.execute("SELECT id FROM colaboradores WHERE nome = ?", (colaborador,)).fetchone()[0]
            cursor.execute("""
                INSERT INTO historico (colaborador_id, pontos, descricao, data)
                VALUES (?, ?, ?, ?)
            """, (colab_id, penalidades[pen], pen, datetime.now()))
            conn.commit()
            st.success("✅ Penalidade aplicada!")
            st.rerun()

    # Ranking Geral
    st.markdown('<div class="section-title">🏆 Ranking Geral</div>', unsafe_allow_html=True)
    query_rank = """
    SELECT 
        c.nome,
        c.pontos_iniciais + IFNULL(SUM(h.pontos),0) pontos
    FROM colaboradores c
    LEFT JOIN historico h ON h.colaborador_id = c.id
    WHERE c.ativo = 1
    GROUP BY c.id
    ORDER BY pontos DESC
    """
    df_rank = pd.read_sql(query_rank, conn)
    df_rank["Recompensa (R$)"] = df_rank["pontos"] * VALOR_PONTO
    st.dataframe(df_rank, use_container_width=True, hide_index=True)

    # Gráfico de Ranking (barras horizontais)
    st.markdown('<div class="section-title">📈 Visualização do Ranking</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Bar(
        x=df_rank["pontos"],
        y=df_rank["nome"],
        orientation='h',
        marker_color='#3b82f6'
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="Pontos",
        yaxis={'categoryorder': 'total ascending'},
        height=250
    )
    st.plotly_chart(fig, use_container_width=True)

# =================================================
# COLUNA DA DIREITA: GESTÃO ADMINISTRATIVA
# =================================================
with col_right:

    # Adicionar Colaborador
    st.markdown('<div class="section-title">➕ Adicionar Colaborador</div>', unsafe_allow_html=True)
    with st.expander("Cadastrar novo colaborador", expanded=False):
        novo = st.text_input("Nome do colaborador")
        if st.button("Adicionar"):
            if novo.strip():
                try:
                    cursor.execute("INSERT INTO colaboradores (nome, pontos_iniciais, ativo) VALUES (?, ?, 1)", (novo, 100))
                    conn.commit()
                    st.success("✅ Colaborador adicionado!")
                    st.rerun()
                except:
                    st.warning("⚠️ Colaborador já existe!")

    # Inativar Colaborador
    st.markdown('<div class="section-title">🛑 Inativar Colaborador</div>', unsafe_allow_html=True)
    df_ativos = pd.read_sql("SELECT nome FROM colaboradores WHERE ativo = 1", conn)
    with st.expander("Desligamento / Inativação", expanded=False):
        colab_inativar = st.selectbox("Selecione", ["Selecione"] + df_ativos["nome"].tolist(), key="inativar")
        confirmar = st.checkbox("Confirmo a inativação")
        if st.button("Inativar"):
            if colab_inativar != "Selecione" and confirmar:
                cursor.execute("UPDATE colaboradores SET ativo = 0 WHERE nome = ?", (colab_inativar,))
                conn.commit()
                st.success("✅ Colaborador inativado!")
                st.rerun()
            else:
                st.warning("⚠️ Selecione e confirme.")

    # Gerenciar Penalidades
    st.markdown('<div class="section-title">📝 Gerenciar Penalidades</div>', unsafe_allow_html=True)
    
    # Adicionar nova
    with st.expander("➕ Nova penalidade", expanded=False):
        desc_nova = st.text_input("Descrição")
        valor_novo = st.number_input("Valor (negativo)", value=-5, step=1, format="%d", key="nova_val")
        if st.button("Salvar"):
            if desc_nova.strip():
                try:
                    cursor.execute("INSERT INTO tipos_penalidade (descricao, valor) VALUES (?, ?)", (desc_nova.strip(), int(valor_novo)))
                    conn.commit()
                    st.success("✅ Salva!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("⚠️ Já existe.")
    
    # Editar/excluir penalidade
    with st.expander("✏️ Editar/Excluir", expanded=False):
        df_pen = pd.read_sql("SELECT id, descricao, valor FROM tipos_penalidade ORDER BY valor", conn)
        if not df_pen.empty:
            sel = st.selectbox("Escolha", df_pen["descricao"].tolist(), key="edit_sel")
            row = df_pen[df_pen["descricao"] == sel].iloc[0]
            new_desc = st.text_input("Descrição", value=row["descricao"], key="ed_desc")
            new_val = st.number_input("Valor", value=int(row["valor"]), step=1, key="ed_val")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Atualizar"):
                    try:
                        cursor.execute("UPDATE tipos_penalidade SET descricao = ?, valor = ? WHERE id = ?", (new_desc.strip(), new_val, row["id"]))
                        conn.commit()
                        st.success("✅ Atualizada!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.warning("⚠️ Descrição duplicada.")
            with c2:
                cursor.execute("SELECT COUNT(*) FROM historico WHERE descricao = ?", (row["descricao"],))
                usada = cursor.fetchone()[0] > 0
                if st.button("🗑️ Excluir", disabled=usada):
                    cursor.execute("DELETE FROM tipos_penalidade WHERE id = ?", (row["id"],))
                    conn.commit()
                    st.success("✅ Excluída!")
                    st.rerun()
                if usada:
                    st.caption("⚠️ Usada no histórico")

    # Histórico com filtro
    st.markdown('<div class="section-title">📜 Histórico (com filtro)</div>', unsafe_allow_html=True)
    if colaborador != "Selecione":
        data_ini = st.date_input("De", value=date.today().replace(day=1), key="hi")
        data_fim = st.date_input("Até", value=date.today(), key="hf")
        data_ini_dt = datetime.combine(data_ini, datetime.min.time())
        data_fim_dt = datetime.combine(data_fim, datetime.max.time())
        hist = pd.read_sql("""
            SELECT descricao, pontos, substr(data, 1, 16) as data
            FROM historico h
            JOIN colaboradores c ON c.id = h.colaborador_id
            WHERE c.nome = ? AND h.data BETWEEN ? AND ?
            ORDER BY data DESC
        """, conn, params=(colaborador, data_ini_dt, data_fim_dt))
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.info("Selecione um colaborador.")

# =================================================
# RODAPÉ (opcional)
# =================================================
st.markdown("<hr style='margin-top: 40px; border: none; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
st.caption("Sistema de Gestão de Pontos • Atualizado em tempo real")