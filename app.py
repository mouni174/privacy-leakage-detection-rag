import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.llm import generate_answer


# =========================================
# Page Configuration
# =========================================

st.set_page_config(
    page_title="Privacy Leakage Detection in RAG",
    page_icon="🔒",
    layout="wide"
)


# =========================================
# Application Title
# =========================================

st.title("🔒 Privacy Leakage Detection in RAG Systems")

st.markdown(
    """
    Upload a PDF, ask questions, and detect sensitive information
    before retrieved content reaches the LLM.
    """
)


# =========================================
# Session State
# =========================================

if "database_ready" not in st.session_state:
    st.session_state.database_ready = False

if "chunks_count" not in st.session_state:
    st.session_state.chunks_count = 0

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = ""


# =========================================
# Sidebar
# =========================================

st.sidebar.title("📊 Project Dashboard")

uploaded_file = st.sidebar.file_uploader(
    "Upload PDF",
    type=["pdf"]
)


# =========================================
# Process PDF
# =========================================

if uploaded_file is not None:

    # Process only when a new PDF is uploaded
    if uploaded_file.name != st.session_state.uploaded_filename:

        st.session_state.database_ready = False
        st.session_state.uploaded_filename = uploaded_file.name

        # Save uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp_file:

            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name

        try:

            with st.spinner("📄 Processing PDF..."):

                # -----------------------------
                # Load and split PDF
                # -----------------------------

                chunks = load_and_split_pdf(pdf_path)

                # -----------------------------
                # Create vector database
                # -----------------------------

                create_vector_store(chunks)

                st.session_state.database_ready = True
                st.session_state.chunks_count = len(chunks)

            st.sidebar.success(
                "✅ PDF Indexed Successfully"
            )

        except Exception as e:

            st.error(
                f"Error processing PDF: {e}"
            )

            st.session_state.database_ready = False

        finally:

            # Remove temporary PDF
            if os.path.exists(pdf_path):
                os.remove(pdf_path)


# =========================================
# Sidebar Analytics
# =========================================

st.sidebar.markdown("---")

st.sidebar.metric(
    "Document Chunks",
    st.session_state.chunks_count
)


# =========================================
# Question Answering
# =========================================

if st.session_state.database_ready:

    st.subheader("💬 Ask Questions")

    question = st.text_input(
        "Enter your question"
    )

    if st.button(
        "🔍 Generate Answer",
        use_container_width=True
    ):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

            st.stop()


        try:

            with st.spinner(
                "🔎 Retrieving relevant information..."
            ):

                # =====================================
                # RAG Retrieval
                # =====================================

                retrieved = get_relevant_context(
                    question
                )


            # =====================================
            # Handle Retriever Result
            # =====================================

            if isinstance(retrieved, dict):

                documents = retrieved.get(
                    "documents",
                    []
                )

                context = retrieved.get(
                    "context",
                    ""
                )

            else:

                # Older retriever versions return
                # context directly

                context = retrieved

                documents = []


            # =====================================
            # Privacy Guardrail
            # =====================================

            with st.spinner(
                "🛡 Checking retrieved information for privacy leakage..."
            ):

                guardrail = process_context(
                    context
                )


            # =====================================
            # Generate LLM Answer
            # =====================================

            with st.spinner(
                "🤖 Generating secure answer..."
            ):

                answer = generate_answer(
                    guardrail["safe_context"],
                    question
                )


            # =====================================
            # Results
            # =====================================

            st.markdown("---")

            col1, col2 = st.columns(2)


            # =====================================
            # LEFT COLUMN
            # =====================================

            with col1:

                st.subheader(
                    "📄 Retrieved Context"
                )

                if documents:

                    for i, document in enumerate(
                        documents
                    ):

                        with st.expander(
                            f"Chunk {i + 1}"
                        ):

                            st.write(
                                document.page_content
                            )

                else:

                    st.text_area(
                        "Retrieved Context",
                        context,
                        height=250
                    )


                # =================================
                # Regex Detection
                # =================================

                st.subheader(
                    "🔍 Regex Privacy Detection"
                )

                st.json(
                    guardrail["regex_findings"]
                )


                # =================================
                # NER Detection
                # =================================

                st.subheader(
                    "🧠 Named Entity Detection"
                )

                st.json(
                    guardrail["ner_findings"]
                )


            # =====================================
            # RIGHT COLUMN
            # =====================================

            with col2:

                # =================================
                # Guardrail Decision
                # =================================

                st.subheader(
                    "🛡 Privacy Guardrail"
                )

                if guardrail["sensitive"]:

                    st.error(
                        "⚠️ Sensitive information detected"
                    )

                else:

                    st.success(
                        "✅ No sensitive information detected"
                    )


                st.write(
                    f"**Action:** {guardrail['action']}"
                )


                # =================================
                # Sanitized Context
                # =================================

                st.subheader(
                    "🔐 Sanitized Context"
                )

                st.text_area(
                    
                    "Content sent to LLM",
                    guardrail["safe_context"],
                    height=250
                )


                # =================================
                # Gemini Answer
                # =================================

                st.subheader(
                    "🤖 Gemini Response"
                )

                st.success(
                    answer
                )


            # =====================================
            # Sidebar Metrics
            # =====================================

            st.sidebar.markdown("---")

            if documents:

                st.sidebar.metric(
                    "Retrieved Chunks",
                    len(documents)
                )


            regex_count = sum(
                len(values)
                for values in guardrail[
                    "regex_findings"
                ].values()
            )


            ner_count = sum(
                len(values)
                for values in guardrail[
                    "ner_findings"
                ].values()
            )


            st.sidebar.metric(
                "Regex Findings",
                regex_count
            )


            st.sidebar.metric(
                "NER Findings",
                ner_count
            )


            st.sidebar.metric(
                "Sensitive Items",
                regex_count + ner_count
            )


            st.sidebar.metric(
                "Guardrail Action",
                guardrail["action"]
            )


        except Exception as e:

            st.error(
                f"Error while processing your question: {e}"
            )


else:

    st.info(
        "📄 Upload a PDF from the sidebar to begin."
    )