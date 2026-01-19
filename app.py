import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CSV / Excel Dashboard", layout="wide")
st.title("📊 CSV / Excel Data Dashboard")

# ----------------------------
# Helper Functions
# ----------------------------
def show_hint(msg):
    st.info(msg, icon="ℹ️")

def numeric_columns(df):
    return df.select_dtypes(include=np.number).columns.tolist()

def categorical_columns(df):
    return df.select_dtypes(exclude=np.number).columns.tolist()

# ----------------------------
# FILE UPLOAD
# ----------------------------
st.markdown(
    """
📁 **Upload CSV / Excel Files**

Upload one or more **CSV (.csv)** or **Excel (.xlsx)** files.  
Each file can be analysed with a set of **EDA visualisations** to understand your data better.
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

selected_file = st.selectbox("Select file to analyze", list(dataframes.keys()))
df = dataframes[selected_file]

st.write(f"### Selected file: {selected_file} ({len(df)} records)")
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
        "• X-axis → categorical column (Route, Stop, School)\n"
        "• Y-axis → numeric column (Count, Distance, Students)"
    )

    x_col = st.selectbox("X-axis", df.columns)
    y_col = st.selectbox("Y-axis", df.columns)

    bar_mode = st.selectbox(
        "Bar Type",
        ["Vertical", "Horizontal", "Grouped", "Stacked"]
    )

    df_plot = df.copy()
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
        "• Y-axis → numeric column\n"
        "• Color → optional category"
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
        "Radar charts compare multiple numeric metrics for ONE category.\n\n"
        "• Category → Route / Stop / School\n"
        "• Metrics → numeric columns only"
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
            values = row.iloc[0]

            fig = go.Figure(
                go.Scatterpolar(
                    r=values.values,
                    theta=metrics,
                    fill="toself"
                )
            )

            fig.update_layout(
                title=f"Radar Chart – {selected_value}",
                polar=dict(radialaxis=dict(visible=True))
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data for selected category.")

# ----------------------------
# PAIR PLOT
# ----------------------------
elif chart_type == "Pair Plot":

    show_hint(
        "Pair plots show distributions and relationships between numeric columns.\n\n"
        "• Requires at least 2 numeric columns"
    )

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

    show_hint(
        "Correlation heatmaps show the strength of relationships between numeric variables.\n\n"
        "• Uses all numeric columns automatically"
    )

    num_df = df.select_dtypes(include=np.number)

    if num_df.shape[1] < 2:
        st.warning("Need at least 2 numeric columns.")
    else:
        corr = num_df.corr()
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

# ----------------------------
# MAP
# ----------------------------
elif chart_type == "Map":

    show_hint(
        "Maps require latitude and longitude columns.\n\n"
        "• Column names must be 'lat' and 'lon'"
    )

    if "lat" in df.columns and "lon" in df.columns:
        st.map(df[["lat", "lon"]])
    else:
        st.warning("Latitude ('lat') and longitude ('lon') columns not found.")
