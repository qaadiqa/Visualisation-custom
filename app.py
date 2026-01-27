import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Data Visualization Studio",
    layout="wide"
)

# -------------------------------------------------
# GLOBAL STYLES + ANIMATIONS
# -------------------------------------------------
st.markdown("""
<style>

/* ---------- BASE ---------- */
html, body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ---------- PAGE TRANSITION ---------- */
.main > div {
    animation: fadeSlide 0.45s ease-in-out;
}

@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ---------- CARDS ---------- */
.card {
    background: white;
    border-radius: 18px;
    padding: 1.5rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.06);
    margin-bottom: 1.5rem;
}

/* ---------- SECTION ---------- */
.section-alt {
    background: #FFFDF8;
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
}

/* ---------- MOBILE ---------- */
@media (max-width: 768px) {
    .card {
        padding: 1rem;
    }
}

/* ---------- CHAT OVERLAY ---------- */
.chat-box {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 320px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    padding: 1rem;
    z-index: 999;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# DARK / LIGHT MODE
# -------------------------------------------------
dark_mode = st.toggle("🌗 Dark Mode")

if dark_mode:
    st.markdown("""
    <style>
    body, .main { background-color: #0E1117; color: #FAFAFA; }
    .card, .chat-box { background-color: #1E1E1E; color: #FAFAFA; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    body, .main { background-color: #FAF9F6; color: #2C2C2C; }
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
Each dataset can be explored using multiple EDA visualizations.
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
# LOAD DATA
# -------------------------------------------------
dataframes = {}
for f in uploaded_files:
    if f.name.endswith(".csv"):
        dataframes[f.name] = pd.read_csv(f)
    else:
        dataframes[f.name] = pd.read_excel(f)

# -------------------------------------------------
# FLOATING FILTER PANEL (SIDEBAR)
# -------------------------------------------------
with st.sidebar:
    st.markdown("## 🎛 Controls")

    selected_file = st.selectbox("Dataset", list(dataframes.keys()))
    df = dataframes[selected_file]

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
# DATA PREVIEW
# -------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader(f"📄 {selected_file} ({len(df)} rows)")
st.dataframe(df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# VISUALIZATIONS
# -------------------------------------------------
st.markdown('<div class="section-alt">', unsafe_allow_html=True)

if chart_type == "Bar Chart":
    st.subheader("📊 Bar Chart")
    st.info("X → categorical | Y → numeric")

    x = st.selectbox("X-axis", df.columns)
    y = st.selectbox("Y-axis", df.columns)

    df[y] = pd.to_numeric(df[y], errors="coerce")

    fig = px.bar(df, x=x, y=y, color_discrete_sequence=colors)
    fig.update_layout(transition_duration=500)
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Scatter Plot":
    st.subheader("📈 Scatter Plot")
    nums = df.select_dtypes(include=np.number).columns

    if len(nums) >= 2:
        x = st.selectbox("X-axis", nums)
        y = st.selectbox("Y-axis", nums)

        fig = px.scatter(df, x=x, y=y, color_discrete_sequence=colors)
        fig.update_layout(transition_duration=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Need at least 2 numeric columns.")

elif chart_type == "Radar Chart":
    st.subheader("🕸 Radar Chart")

    cat = st.selectbox("Category column", df.columns)
    metrics = st.multiselect(
        "Numeric metrics",
        df.select_dtypes(include=np.number).columns
    )

    if metrics:
        value = st.selectbox("Category value", df[cat].unique())
        row = df[df[cat] == value][metrics]

        if not row.empty:
            fig = go.Figure(
                go.Scatterpolar(
                    r=row.iloc[0].values,
                    theta=metrics,
                    fill="toself"
                )
            )
            fig.update_layout(title=value)
            st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Pair Plot":
    st.subheader("🔗 Pair Plot")
    nums = df.select_dtypes(include=np.number)

    if nums.shape[1] >= 2:
        fig = sns.pairplot(nums)
        st.pyplot(fig)
    else:
        st.warning("Not enough numeric columns.")

elif chart_type == "Correlation Heatmap":
    st.subheader("🔥 Correlation Heatmap")
    nums = df.select_dtypes(include=np.number)

    if nums.shape[1] >= 2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(nums.corr(), annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Not enough numeric columns.")

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# LLM CHAT OVERLAY (UI READY)
# -------------------------------------------------
st.markdown("""
<div class="chat-box">
<h4>🧠 Ask your data</h4>
<p style="font-size: 0.85rem;">
Example: <i>"Show average students per route"</i>
</p>
</div>
""", unsafe_allow_html=True)
