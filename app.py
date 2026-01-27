import streamlit as st
import pandas as pd
import numpy as np
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import requests

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config("Smart Data Dashboard", layout="wide")

# ----------------------------
# FONT
# ----------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# LIGHT / DARK MODE
# ----------------------------
dark = st.toggle("🌗 Dark Mode")
st.markdown(f"""
<style>
.stApp {{
    background-color: {"#0E1117" if dark else "#FAF9F6"};
    color: {"#EDEDED" if dark else "#1F2937"};
}}
h1,h2,h3,h4,h5,p,label {{
    color: {"#EDEDED" if dark else "#1F2937"} !important;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# TITLE
# ----------------------------
st.title("📊 Power AID")

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
# SQL QUERY UI (REPLACED)
# -------------------------------------------------
st.markdown("---")
st.header("🧠 SQL Query Engine")

st.markdown("**Available Tables:**")
table_map = {f.name.replace(".", "_").replace(" ", "_"): f.name for f in uploaded_files}
for f, t in table_map.items():
    st.code(f"{t}  ←  {f}")

sql_query = st.text_area(
    "Write SQL query",
    height=180,
    placeholder="""
Example:
SELECT route, COUNT(*) AS total_students
FROM route_details
GROUP BY route
"""
)

if st.button("▶ Run Query"):
    try:
        sql_result = con.execute(sql_query).df()
        st.success(f"Query executed successfully ({len(sql_result)} rows)")
        st.dataframe(sql_result, use_container_width=True)
        st.session_state["sql_result"] = sql_result
    except Exception as e:
        st.error(f"SQL Error: {e}")

# ----------------------------
# DATA SOURCE SELECTION
# ----------------------------
st.markdown("---")
st.header("📂 Data Source")

selected_file = st.selectbox("Select original file", list(dataframes.keys()))
df_original = dataframes[selected_file]

use_sql = False
if "sql_result" in st.session_state:
    use_sql = st.checkbox("Use SQL query result for visualization", value=True)

df_viz = st.session_state["sql_result"] if use_sql else df_original

st.write(f"### Active Dataset ({len(df_viz)} records)")
st.dataframe(df_viz, use_container_width=True)

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
st.subheader("🧠 A
