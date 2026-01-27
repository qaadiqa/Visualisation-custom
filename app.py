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
st.title("📊 Intelligent Data Dashboard")

# ----------------------------
# FILE UPLOAD
# ----------------------------
files = st.file_uploader(
    "📁 Upload CSV / Excel Files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if not files:
    st.info("Upload files to begin")
    st.stop()

# ----------------------------
# LOAD INTO DUCKDB
# ----------------------------
con = duckdb.connect()
dfs = {}

for f in files:
    name = f.name.replace(".", "_")
    if f.name.endswith(".csv"):
        df = pd.read_csv(f)
    else:
        df = pd.read_excel(f)

    dfs[name] = df
    con.register(name, df)

# ----------------------------
# SCHEMA CONTEXT
# ----------------------------
def schema_context():
    text = ""
    for k, v in dfs.items():
        text += f"Table {k}: {', '.join(v.columns)}\n"
    return text

# ----------------------------
# AUTO CHART
# ----------------------------
def auto_chart(df):
    num = df.select_dtypes(include=np.number).columns
    cat = df.select_dtypes(exclude=np.number).columns

    if {"lat", "lon"}.issubset(df.columns):
        return "map"
    if len(num) == 1 and len(cat) >= 1:
        return "bar"
    if len(num) == 2 and len(cat) == 0:
        return "scatter"
    if len(num) > 2:
        return "heatmap"
    if len(num) >= 3 and len(cat) == 1:
        return "radar"
    return "table"

# ----------------------------
# LOCAL LLM → SQL
# ----------------------------
def generate_sql(prompt):
    payload = {
        "model": "llama3",
        "prompt": f"""
Generate ONLY DuckDB SQL.
No explanation.

Schema:
{schema_context()}

User question:
{prompt}
"""
    }
    r = requests.post("http://localhost:11434/api/generate", json=payload)
    r.raise_for_status()
    return r.json()["response"]

# ----------------------------
# CHAT / SQL
# ----------------------------
st.subheader("🧠 Ask Your Data")

question = st.text_input("Ask a question (natural language → SQL)")

if st.button("Run"):
    try:
        sql = generate_sql(question)
        st.code(sql, language="sql")

        result = con.execute(sql).df()
        st.dataframe(result, use_container_width=True)

        chart = auto_chart(result)

        st.subheader("📊 Auto Visualization")

        if chart == "bar":
            fig = px.bar(result, x=result.columns[0], y=result.columns[1])
            st.plotly_chart(fig, use_container_width=True)

        elif chart == "scatter":
            fig = px.scatter(result, x=result.columns[0], y=result.columns[1])
            st.plotly_chart(fig, use_container_width=True)

        elif chart == "heatmap":
            corr = result.corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr, annot=True, ax=ax)
            st.pyplot(fig)

        elif chart == "radar":
            row = result.iloc[0]
            fig = go.Figure(go.Scatterpolar(
                r=row.values,
                theta=row.index,
                fill="toself"
            ))
            st.plotly_chart(fig)

        elif chart == "map":
            st.map(result[["lat", "lon"]])

        else:
            st.info("Displayed as table")

    except Exception as e:
        st.error(str(e))
