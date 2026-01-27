import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import duckdb

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Data Visualization Studio", layout="wide")

# -------------------------------------------------
# GLOBAL STYLES + ANIMATIONS
# -------------------------------------------------
st.markdown("""
<style>
.main > div {
    animation: fadeSlide 0.4s ease-in-out;
}
@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.card {
    border-radius: 18px;
    padding: 1.5rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    margin-bottom: 1.5rem;
}
.section-alt {
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
}
@media (max-width: 768px) {
    .card { padding: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# LIGHT / DARK MODE (FIXED)
# -------------------------------------------------
dark_mode = st.toggle("🌗 Dark Mode")

if dark_mode:
    st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .card, .section-alt { background-color: #1E1E1E; color: #FAFAFA; }
    section[data-testid="stSidebar"] { background-color: #161A23; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background-color: #FAF9F6; color: #2C2C2C; }
    .card, .section-alt { background-color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("📊 Data Visualization Studio")

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("""
📁 **Upload CSV / Excel Files**  
Upload one or more **CSV (.csv)** or **Excel (.xlsx)** files.  
Each dataset can be analysed using EDA visualisations or SQL queries.
""")

uploaded_files = st.file_uploader(
    "Upload files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)
st.markdown('</div>', unsafe_allow_html=True)

if not uploaded_files:
    st.info("Upload files to begin.")
    st.stop()

# -------------------------------------------------
# LOAD FILES + DUCKDB
# -------------------------------------------------
dataframes = {}
con = duckdb.connect(database=":memory:")

for f in uploaded_files:
    if f.name.endswith(".csv"):
        df_tmp = pd.read_csv(f)
    else:
        df_tmp = pd.read_excel(f)

    table_name = f.name.replace(".", "_").replace(" ", "_")
    dataframes[f.name] = df_tmp
    con.register(table_name, df_tmp)

# -------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------
with st.sidebar:
    st.header("🎛 Controls")

    selected_file = st.selectbox("Dataset", list(dataframes.keys()))
    chart_type = st.selectbox(
        "Visualization",
        [
            "Bar Chart",
            "Scatter Plot",
            "Radar Chart",
            "Pair Plot",
            "Correlation Heatmap"
        ]
    )

    palette_name = st.selectbox(
        "🎨 Color Palette",
        ["Default", "Pastel", "Bold", "Dark", "Sunset"]
    )

palette_map = {
    "Default": px.colors.qualitative.Plotly,
    "Pastel": px.colors.qualitative.Pastel,
    "Bold": px.colors.qualitative.Bold,
    "Dark": px.colors.qualitative.Dark24,
    "Sunset": px.colors.sequential.Sunset
}

colors = palette_map[palette_name]

# -------------------------------------------------
# DATA SOURCE (RAW OR SQL RESULT)
# -------------------------------------------------
df_base = dataframes[selected_file]
df_viz = st.session_state.get("sql_result", df_base)

# -------------------------------------------------
# DATA PREVIEW
# -------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader(f"📄 Preview ({len(df_viz)} rows)")
st.dataframe(df_viz, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# SQL QUERY EDITOR (REAL)
# -------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🧮 SQL Query Editor")

st.info(
    "Each uploaded file is available as a SQL table.\n"
    "Table name = file name with dots replaced by underscores."
)

sql_query = st.text_area(
    "Write SQL query",
    height=150,
    placeholder="SELECT * FROM your_file_csv LIMIT 10;"
)

if st.button("Run Query"):
    try:
        result = con.execute(sql_query).df()
        st.session_state["sql_result"] = result
        st.success(f"Query returned {len(result)} rows")
    except Exception as e:
        st.error(str(e))

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# VISUALIZATIONS
# -------------------------------------------------
st.markdown('<div class="section-alt">', unsafe_allow_html=True)

if chart_type == "Bar Chart":
    st.subheader("📊 Bar Chart")
    st.info("X → categorical | Y → numeric")

    x = st.selectbox("X-axis", df_viz.columns)
    y = st.selectbox("Y-axis", df_viz.columns)

    df_viz[y] = pd.to_numeric(df_viz[y], errors="coerce")
    fig = px.bar(df_viz, x=x, y=y, color_discrete_sequence=colors)
    fig.update_layout(transition_duration=500)
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Scatter Plot":
    st.subheader("📈 Scatter Plot")
    nums = df_viz.select_dtypes(include=np.number).columns

    if len(nums) >= 2:
        x = st.selectbox("X-axis", nums)
        y = st.selectbox("Y-axis", nums)
        fig = px.scatter(df_viz, x=x, y=y, color_discrete_sequence=colors)
        fig.update_layout(transition_duration=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Need at least two numeric columns.")

elif chart_type == "Radar Chart":
    st.subheader("🕸 Radar Chart")
    cat = st.selectbox("Category column", df_viz.columns)
    metrics = st.multiselect(
        "Numeric metrics",
        df_viz.select_dtypes(include=np.number).columns
    )

    if metrics:
        val = st.selectbox("Category value", df_viz[cat].unique())
        row = df_viz[df_viz[cat] == val][metrics]

        if not row.empty:
            fig = go.Figure(
                go.Scatterpolar(
                    r=row.iloc[0].values,
                    theta=metrics,
                    fill="toself"
                )
            )
            fig.update_layout(title=val)
            st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Pair Plot":
    st.subheader("🔗 Pair Plot")
    nums = df_viz.select_dtypes(include=np.number)
    if nums.shape[1] >= 2:
        fig = sns.pairplot(nums)
        st.pyplot(fig)
    else:
        st.warning("Not enough numeric columns.")

elif chart_type == "Correlation Heatmap":
    st.subheader("🔥 Correlation Heatmap")
    nums = df_viz.select_dtypes(include=np.number)
    if nums.shape[1] >= 2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(nums.corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Not enough numeric columns.")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# CHATBOT (REAL STATEFUL)
# -------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🧠 Ask Your Data (Chatbot)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input(
    "Ask a question (e.g. total students per route)"
)

if st.button("Ask"):
    if question:
        st.session_state.chat_history.append(("You", question))
        st.session_state.chat_history.append(
            ("Assistant", "LLM integration coming next (SQL generation).")
        )

for role, msg in st.session_state.chat_history:
    st.markdown(f"**{role}:** {msg}")

st.markdown('</div>', unsafe_allow_html=True)
