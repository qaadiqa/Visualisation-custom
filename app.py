import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import re

st.set_page_config(page_title="CSV / Excel Dashboard", layout="wide")
st.title("📊 CSV / Excel Data Dashboard")

# ----------------------------
# Helper Functions
# ----------------------------
def show_hint(msg):
    st.info(msg, icon="ℹ️")

def numeric_columns(df):
    return df.select_dtypes(include=np.number).columns.tolist()

def safe_table_name(name):
    name = re.sub(r"\W+", "_", name.lower())
    return name.replace("_csv", "").replace("_xlsx", "")

# ----------------------------
# FILE UPLOAD
# ----------------------------
st.markdown(
    """
📁 **Upload CSV / Excel Files**

Upload one or more **CSV (.csv)** or **Excel (.xlsx)** files.  
You can query across files using SQL and visualize derived results.
"""
)

uploaded_files = st.file_uploader(
    "Upload files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload one or more CSV / Excel files to begin.")
    st.stop()

# ----------------------------
# LOAD FILES
# ----------------------------
dataframes = {}
for f in uploaded_files:
    if f.name.endswith(".csv"):
        dataframes[f.name] = pd.read_csv(f)
    else:
        dataframes[f.name] = pd.read_excel(f)

# ----------------------------
# SQL ENGINE (DuckDB)
# ----------------------------
con = duckdb.connect(database=":memory:")
table_map = {}

for fname, df_ in dataframes.items():
    table = safe_table_name(fname)
    table_map[fname] = table
    con.register(table, df_)

# ----------------------------
# SQL QUERY UI
# ----------------------------
st.markdown("---")
st.header("🧠 SQL Query Engine")

st.markdown("**Available Tables:**")
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

df = st.session_state["sql_result"] if use_sql else df_original

st.write(f"### Active Dataset ({len(df)} records)")
st.dataframe(df, use_container_width=True)

# ----------------------------
# VISUALIZATION SELECTOR
# ----------------------------
st.markdown("---")
st.header("📊 Visualizations")

chart_type = st.selectbox(
    "Choose Visualization",
    [
        "Bar Chart",
        "Scatter Plot",
        "Spider / Radar Chart",
        "Pair Plot",
        "Correlation Heatmap",
        "Map"
    ]
)

# ----------------------------
# BAR CHART
# ----------------------------
if chart_type == "Bar Chart":

    show_hint(
        "Bar charts compare numeric values across categories.\n\n"
        "• X-axis → categorical column\n"
        "• Y-axis → numeric column"
    )

    x_col = st.selectbox("X-axis", df.columns)
    y_col = st.selectbox("Y-axis", df.columns)

    bar_mode = st.selectbox(
        "Bar Type",
        ["Vertical", "Horizontal", "Grouped", "Stacked"]
    )

    df_plot = df.copy()
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce")
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce")
    st.write(df_plot[[x_col, y_col]])  # Check values
    df_plot[y_col] = df_plot[y_col].astype(str).str.replace(",", "").str.strip()
    df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors="coerce")



    if bar_mode == "Vertical":
        fig = px.bar(df_plot, x=x_col, y=y_col)

    elif bar_mode == "Horizontal":
        fig = px.bar(df_plot, x=y_col, y=x_col, orientation="h")

    elif bar_mode == "Grouped":
        group_col = st.selectbox("Group by", df.columns)
        fig = px.bar(df_plot, x=x_col, y=y_col, color=group_col, barmode="group")

    elif bar_mode == "Stacked":
        stack_col = st.selectbox("Stack by", df.columns)
        fig = px.bar(df_plot, x=x_col, y=y_col, color=stack_col, barmode="stack")

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# SCATTER PLOT
# ----------------------------
elif chart_type == "Scatter Plot":

    show_hint(
        "Scatter plots show relationships between two numeric variables.\n\n"
        "• X-axis → numeric column\n"
        "• Y-axis → numeric column"
    )

    num_cols = numeric_columns(df)

    if len(num_cols) < 2:
        st.warning("Need at least two numeric columns.")
    else:
        x_col = st.selectbox("X-axis (numeric)", num_cols)
        y_col = st.selectbox("Y-axis (numeric)", num_cols)
        color_col = st.selectbox("Color (optional)", ["None"] + list(df.columns))

        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=None if color_col == "None" else color_col
        )

        st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# SPIDER / RADAR CHART
# ----------------------------
elif chart_type == "Spider / Radar Chart":

    show_hint(
        "Radar charts compare multiple numeric metrics for ONE category."
    )

    category_col = st.selectbox("Category column", df.columns)
    metrics = st.multiselect("Numeric metrics", numeric_columns(df))

    if metrics:
        selected_value = st.selectbox(
            "Select category value",
            df[category_col].dropna().unique()
        )

        row = df[df[category_col] == selected_value][metrics]

        if not row.empty:
            fig = go.Figure(
                go.Scatterpolar(
                    r=row.iloc[0].values,
                    theta=metrics,
                    fill="toself"
                )
            )
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title=f"Radar Chart – {selected_value}"
            )
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# PAIR PLOT
# ----------------------------
elif chart_type == "Pair Plot":

    show_hint("Pair plots require at least two numeric columns.")

    num_cols = numeric_columns(df)

    if len(num_cols) < 2:
        st.warning("Not enough numeric columns.")
    else:
        hue = st.selectbox("Hue (optional)", ["None"] + list(df.columns))
        fig = sns.pairplot(
            df[num_cols + ([hue] if hue != "None" else [])],
            hue=None if hue == "None" else hue
        )
        st.pyplot(fig)

# ----------------------------
# CORRELATION HEATMAP
# ----------------------------
elif chart_type == "Correlation Heatmap":

    show_hint("Correlation heatmaps show relationships between numeric variables.")

    num_df = df.select_dtypes(include=np.number)

    if num_df.shape[1] < 2:
        st.warning("Need at least 2 numeric columns.")
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(num_df.corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

# ----------------------------
# MAP
# ----------------------------
elif chart_type == "Map":

    show_hint("Requires 'lat' and 'lon' columns.")

    if "lat" in df.columns and "lon" in df.columns:
        st.map(df[["lat", "lon"]])
    else:
        st.warning("Latitude and longitude columns not found.")
