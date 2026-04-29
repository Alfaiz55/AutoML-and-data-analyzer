from db import init_db, save_result, get_history
init_db()

import streamlit as st
import pandas as pd
import tempfile
from pipe import run_pipeline

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AutoML Analyzer",
    layout="centered"
)

# =========================
# ADMIN PANEL
# =========================
st.sidebar.markdown("### 🔒 Admin Panel")

admin_mode = st.sidebar.checkbox("Enable Admin Mode")
admin_authenticated = False

if admin_mode:
    password = st.sidebar.text_input("Enter Admin Password", type="password")

    if password == "admin123":
        admin_authenticated = True
        st.sidebar.success("Access Granted")
    elif password:
        st.sidebar.error("Wrong Password")

# =========================
# MOBILE CSS
# =========================
st.markdown("""
<style>
.block-container {
    padding: 0.8rem;
}
button[kind="primary"] {
    width: 100% !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.title("🤖 AutoML Analyzer")

# =========================
# STATE
# =========================
if "df" not in st.session_state:
    st.session_state.df = None

if "result" not in st.session_state:
    st.session_state.result = None

# =========================
# TABS (MOBILE NAVIGATION)
# =========================
tab1, tab2, tab3 = st.tabs(["📂 Upload", "⚙️ Setup", "📊 Results"])

# =========================
# 📂 TAB 1: UPLOAD
# =========================
with tab1:
    st.subheader("Upload Dataset")

    uploaded_file = st.file_uploader(
        "Choose file",
        type=["csv", "xlsx", "xls", "docx"]
    )

    if uploaded_file:
        file_ext = uploaded_file.name.split(".")[-1].lower()

        if file_ext == "csv":
            try:
                df = pd.read_csv(uploaded_file)
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="latin1")

        elif file_ext in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)

        elif file_ext == "docx":
            from docx import Document
            doc = Document(uploaded_file)
            data = [[cell.text.strip() for cell in row.cells] for row in doc.tables[0].rows]
            df = pd.DataFrame(data[1:], columns=data[0])

        else:
            st.error("Unsupported file")
            df = None

        if df is not None:
            st.session_state.df = df
            st.success("File loaded successfully")

# =========================
# ⚙️ TAB 2: SETUP
# =========================
with tab2:
    if st.session_state.df is None:
        st.info("Upload dataset first")
    else:
        df = st.session_state.df.copy()

        st.subheader("Preview")
        st.dataframe(df.head(), use_container_width=True)

        drop_cols = st.multiselect("Drop Columns", df.columns)
        if drop_cols:
            df = df.drop(columns=drop_cols)

        target = st.selectbox("Target Column", ["None"] + list(df.columns))
        if target == "None":
            target = None

        if st.button("🚀 Run Analysis"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                df.to_csv(tmp.name, index=False)
                file_path = tmp.name

            result = run_pipeline(file_path, target)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.result = result
                save_result("uploaded_file", result)
                st.success("Analysis completed")

# =========================
# 📊 TAB 3: RESULTS
# =========================
with tab3:
    if st.session_state.result is None:
        st.info("Run analysis first")
    else:
        result = st.session_state.result

        st.subheader("Result Summary")

        st.success(f"""
        Problem Type: {result['problem_type']}
        Best Model: {result['best_model']}
        Score: {round(result['score'], 4)}
        """)

        st.subheader("Model Comparison")

        results = result.get("all_results", {})
        results = {k: v for k, v in results.items() if "BEST" not in k}

        if results:
            df_models = pd.DataFrame(results.items(), columns=["Model", "Score"])
            st.dataframe(df_models.sort_values(by="Score", ascending=False), use_container_width=True)

        with st.expander("🧠 Insights"):
            st.write(result.get("insights", ""))

        if result.get("plots"):
            for fig in result["plots"]:
                st.pyplot(fig, use_container_width=True)

# =========================
# ADMIN HISTORY
# =========================
if admin_authenticated:
    st.subheader("Admin History")

    history = get_history()

    if history:
        df_history = pd.DataFrame(history)
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("No history found.")
