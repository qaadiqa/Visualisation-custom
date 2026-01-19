import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

st.set_page_config(page_title="CSV Dashboard", layout="wide")
st.title("CSV / Excel Dashboard")

# ----------------------------
# FILE UPLOAD (CSV + EXCEL)
# ----------------------------
st.markdown(
    """
📁 **Upload CSV / Excel Files**

Upload one or more **CSV (.csv) or Excel (.xlsx)** files.  
Each file can be analysed with multiple **EDA visualisations** to understand your data better.
"""
)

uploaded_files = st.file_uploader(
    "Upload files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:

    dataframes = {}
    for f in uploaded_files:
        if f.name.endswith(".csv"):
            dataframes[f.name] = pd.read_csv(f)
        else:
            dataframes[f.name] = pd.read_excel(f)

    selected_file = st.selectbox("Select file to analyze", list(dataframes.keys()))
    df = dataframes[selected_file]

    st.write(f"### Selected file: {selected_file} ({len(df)} records)")
    st.dataframe(df)

    # ----------------------------
    # BAR CHARTS
    # ----------------------------
    st.markdown("---")
    st.header("Bar Charts")

    col_x = st.selectbox("X-axis", df.columns, key="bar_x")
    col_y = st.selectbox("Y-axis", df.columns, key="bar_y")

    chart_type = st.selectbox(
        "Bar Chart Type",
        ["Vertical Bar", "Horizontal Bar", "Grouped Bar", "Stacked Bar"]
    )

    df_plot = df.copy()

    if not np.issubdtype(df_plot[col_y].dtype, np.number):
        df_plot[col_y] = pd.to_numeric(df_plot[col_y], errors="coerce")

    if chart_type == "Vertical Bar":
        fig = px.bar(df_plot, x=col_x, y=col_y)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Horizontal Bar":
        fig = px.bar(df_plot, x=col_y, y=col_x, orientation="h")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Grouped Bar":
        group_col = st.selectbox("Group by", df.columns)
        fig = px.bar(df_plot, x=col_x, y=col_y, color=group_col, barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Stacked Bar":
        stack_col = st.selectbox("Stack by", df.columns)
        fig = px.bar(df_plot, x=col_x, y=col_y, color=stack_col, barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # SCATTER PLOTS
    # ----------------------------
    st.markdown("---")
    st.header("Scatter Plot")

    scatter_x = st.selectbox("X-axis", df.columns, key="scatter_x")
    scatter_y = st.selectbox("Y-axis", df.columns, key="scatter_y")
    scatter_color = st.selectbox("Color (optional)", ["None"] + list(df.columns))
    scatter_size = st.selectbox("Size (optional)", ["None"] + list(df.columns))

    fig = px.scatter(
        df,
        x=scatter_x,
        y=scatter_y,
        color=None if scatter_color == "None" else scatter_color,
        size=None if scatter_size == "None" else scatter_size
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # PAIR PLOT / FACET GRID
    # ----------------------------
    st.markdown("---")
    st.header("Pair Plot / Facet Grid")

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    if len(numeric_cols) >= 2:
        hue_col = st.selectbox("Hue (optional)", ["None"] + list(df.columns))
        fig = sns.pairplot(df[numeric_cols + ([hue_col] if hue_col != "None" else [])],
                           hue=None if hue_col == "None" else hue_col)
        st.pyplot(fig)
    else:
        st.warning("Need at least two numeric columns for pair plots.")

    # ----------------------------
    # SPIDER / RADAR CHART (ROUTE DETAILS)
    # ----------------------------
    st.markdown("---")
    st.header("🕸 Spider / Radar Chart (Route Comparison)")

    category_col = st.selectbox("Category (Route / Stop / School)", df.columns)

    value_cols = st.multiselect(
        "Numeric metrics to compare",
        df.select_dtypes(include=np.number).columns
    )

    if category_col and value_cols:
        selected_category = st.selectbox(
            "Select category value",
            df[category_col].unique()
        )

        row = df[df[category_col] == selected_category][value_cols].iloc[0]

        fig = go.Figure(
            data=[
                go.Scatterpolar(
                    r=row.values,
                    theta=value_cols,
                    fill="toself"
                )
            ]
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title=f"Spider Chart for {selected_category}"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # BASIC MAP (UNCHANGED)
    # ----------------------------
    st.markdown("---")
    st.header("🗺 Basic Map Plot")

    if "lat" in df.columns and "lon" in df.columns:
        st.map(df[["lat", "lon"]])
    else:
        st.info("Latitude & longitude not found. Map skipped.")

else:
    st.info("Upload one or more CSV / Excel files to begin.")
