import os
import shutil

import streamlit as st

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_ollama import OllamaLLM


# =========================================================
# APPLICATION SETTINGS
# =========================================================

st.set_page_config(
    page_title="Enterprise HR Policy AI Assistant",
    page_icon="👨‍💼",
    layout="wide"
)

DOCUMENT_FOLDER = "documents"
CHROMA_FOLDER = "chroma_db"

os.makedirs(DOCUMENT_FOLDER, exist_ok=True)


# =========================================================
# APPLICATION HEADER
# =========================================================

st.title("👨‍💼 Enterprise HR Policy AI Assistant")

st.write(
    "An AI-powered Retrieval-Augmented Generation (RAG) solution "
    "for answering employee questions using approved HR policy documents."
)

st.caption(
    "📚 Policy Knowledge Base  •  🔎 Semantic Retrieval  •  🤖 AI-Generated Answers  •  "
    "📑 Source References"
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ AI Configuration")

    model_name = st.selectbox(
        "Language Model",
        [
            "qwen2.5:1.5b",
        ]
    )

    st.caption(
        "The language model runs locally through Ollama."
    )

    st.divider()

    st.subheader("📄 Knowledge Document")

    uploaded_file = st.file_uploader(
        "Upload HR Policy Document (PDF)",
        type=["pdf"],
        help=(
            "Upload an HR policy document that will be "
            "used as the knowledge source for the AI assistant."
        )
    )

    st.divider()

    st.subheader("🗑️ Knowledge Base Management")

    if st.button(
        "Clear Knowledge Base",
        use_container_width=True
    ):

        # Clear Streamlit cache first
        st.cache_resource.clear()

        # Remove vector database
        if os.path.exists(CHROMA_FOLDER):

            try:

                shutil.rmtree(CHROMA_FOLDER)

                st.session_state.pop(
                    "vector_db",
                    None
                )

                st.success(
                    "Knowledge base cleared successfully."
                )

                st.rerun()

            except PermissionError:

                st.error(
                    "ChromaDB is currently being used. "
                    "Please stop Streamlit, delete the "
                    "'chroma_db' folder, and restart the application."
                )

            except Exception as e:

                st.error(
                    f"Could not clear the knowledge base: {e}"
                )

        else:

            st.info(
                "No knowledge base is currently available."
            )


# =========================================================
# EMBEDDING MODEL
# =========================================================

@st.cache_resource
def load_embeddings():

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


embeddings = load_embeddings()


# =========================================================
# CREATE VECTOR DATABASE
# =========================================================

def create_vector_database(pdf_path):

    st.info(
        "📖 Reading and processing the HR policy document..."
    )

    # -----------------------------------------------------
    # LOAD PDF
    # -----------------------------------------------------

    loader = PyPDFLoader(pdf_path)

    documents = loader.load()

    st.write(
        f"📄 **Policy pages identified:** {len(documents)}"
    )

    # -----------------------------------------------------
    # SPLIT DOCUMENT INTO CHUNKS
    # -----------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    st.write(
        f"🧩 **Knowledge chunks created:** {len(chunks)}"
    )

    # -----------------------------------------------------
    # IMPORTANT
    #
    # DO NOT DELETE CHROMA DATABASE HERE.
    #
    # Streamlit reruns the application frequently.
    # Deleting the database here can cause:
    #
    # PermissionError: [WinError 32]
    #
    # -----------------------------------------------------

    # Create the Chroma vector database
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_FOLDER
    )

    return vector_db, len(documents), len(chunks)


# =========================================================
# PROCESS UPLOADED PDF
# =========================================================

if uploaded_file:

    pdf_path = os.path.join(
        DOCUMENT_FOLDER,
        uploaded_file.name
    )

    # Save uploaded PDF
    with open(pdf_path, "wb") as f:

        f.write(
            uploaded_file.getbuffer()
        )

    st.success(
        f"📄 Document uploaded successfully: **{uploaded_file.name}**"
    )

    # -----------------------------------------------------
    # BUILD KNOWLEDGE BASE
    # -----------------------------------------------------

    if st.button(
        "🔨 Build Knowledge Base",
        use_container_width=True
    ):

        with st.spinner(
            "Building the HR policy knowledge base..."
        ):

            try:

                vector_db, pages, chunks = (
                    create_vector_database(
                        pdf_path
                    )
                )

                # Store database in session
                st.session_state["vector_db"] = (
                    vector_db
                )

                st.success(
                    "✅ HR policy knowledge base created successfully!"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "📄 Policy Pages",
                        pages
                    )

                with col2:

                    st.metric(
                        "🧩 Knowledge Chunks",
                        chunks
                    )

            except Exception as e:

                st.error(
                    f"Error creating knowledge base: {e}"
                )


# =========================================================
# LOAD EXISTING VECTOR DATABASE
# =========================================================

if (
    "vector_db" not in st.session_state
    and os.path.exists(CHROMA_FOLDER)
):

    try:

        st.session_state["vector_db"] = Chroma(
            persist_directory=CHROMA_FOLDER,
            embedding_function=embeddings
        )

    except Exception as e:

        st.warning(
            f"Could not load the existing knowledge base: {e}"
        )


# =========================================================
# RAG WORKFLOW EXPLANATION
# =========================================================

st.divider()

st.subheader(
    "🔄 RAG Workflow"
)

workflow_col1, workflow_col2, workflow_col3, workflow_col4, workflow_col5 = (
    st.columns(5)
)

with workflow_col1:

    st.markdown(
        "### 📄\nUpload"
    )

    st.caption(
        "Upload the HR policy document."
    )

with workflow_col2:

    st.markdown(
        "### 🧩\nChunk"
    )

    st.caption(
        "Split the document into searchable sections."
    )

with workflow_col3:

    st.markdown(
        "### 🧠\nEmbed"
    )

    st.caption(
        "Convert policy text into semantic vectors."
    )

with workflow_col4:

    st.markdown(
        "### 🔎\nRetrieve"
    )

    st.caption(
        "Find the most relevant policy content."
    )

with workflow_col5:

    st.markdown(
        "### 🤖\nGenerate"
    )

    st.caption(
        "Generate an answer using retrieved policy context."
    )


# =========================================================
# DASHBOARD
# =========================================================

st.divider()

st.subheader(
    "📊 AI Assistant Overview"
)

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "📚 Knowledge Base",
        "HR Policy Documents"
    )


with col2:

    st.metric(
        "🧠 Embedding Model",
        "MiniLM"
    )


with col3:

    st.metric(
        "🤖 Language Model",
        model_name
    )


# =========================================================
# KNOWLEDGE BASE STATUS
# =========================================================

st.divider()

if "vector_db" in st.session_state:

    st.success(
        "🟢 **Knowledge Base Ready** — "
        "The HR policy document has been processed and is ready for questions."
    )

else:

    st.info(
        "🔵 **Knowledge Base Not Ready** — "
        "Upload an HR policy PDF and build the knowledge base to begin."
    )


# =========================================================
# QUESTION AREA
# =========================================================

st.divider()

st.subheader(
    "💬 Ask the HR Policy Assistant"
)

st.write(
    "Ask a natural-language question about the HR policies. "
    "The assistant will retrieve relevant policy content and "
    "generate an answer based on that information."
)

question = st.text_input(
    "Employee Policy Question",
    placeholder=(
        "Example: How many annual leave days can an employee take?"
    )
)


# =========================================================
# RAG PROCESS
# =========================================================

if st.button(
    "🔍 Get Policy Answer",
    use_container_width=True
):

    # -----------------------------------------------------
    # VALIDATE QUESTION
    # -----------------------------------------------------

    if not question:

        st.warning(
            "Please enter an HR policy question."
        )

    # -----------------------------------------------------
    # CHECK VECTOR DATABASE
    # -----------------------------------------------------

    elif "vector_db" not in st.session_state:

        st.error(
            "Please upload an HR policy document and "
            "build the knowledge base before asking a question."
        )

    else:

        vector_db = (
            st.session_state["vector_db"]
        )

        # -------------------------------------------------
        # RETRIEVAL
        # -------------------------------------------------

        with st.spinner(
            "🔎 Searching the HR policy knowledge base..."
        ):

            results = (
                vector_db.similarity_search(
                    question,
                    k=4
                )
            )

        # -------------------------------------------------
        # NO RESULTS
        # -------------------------------------------------

        if not results:

            st.warning(
                "No relevant HR policy information "
                "was found for this question."
            )

        else:

            # -------------------------------------------------
            # BUILD CONTEXT
            # -------------------------------------------------

            context = "\n\n".join(
                [
                    document.page_content
                    for document in results
                ]
            )

            # -------------------------------------------------
            # PROMPT
            # -------------------------------------------------

            prompt = f"""
You are an Enterprise HR Policy Assistant.

Your responsibility is to answer employee questions
using ONLY the HR policy information provided below.

IMPORTANT RULES:

1. Do not invent or create HR policies.
2. Do not assume information that is not explicitly provided.
3. Do not use outside knowledge.
4. If the answer is not available in the provided policy,
   say exactly:

"I could not find this information in the HR policy."

5. Provide a clear, concise, and professional answer.
6. When possible, mention the relevant policy section.
7. Base your answer only on the retrieved policy information.

-----------------------------------------
RETRIEVED HR POLICY INFORMATION
-----------------------------------------

{context}

-----------------------------------------
EMPLOYEE QUESTION
-----------------------------------------

{question}

-----------------------------------------
ANSWER
-----------------------------------------
"""

            # -------------------------------------------------
            # LLM
            # -------------------------------------------------

            llm = OllamaLLM(
                model=model_name,
                temperature=0
            )

            with st.spinner(
                "🤖 Generating a policy-grounded answer..."
            ):

                answer = llm.invoke(
                    prompt
                )

            # -------------------------------------------------
            # ANSWER
            # -------------------------------------------------

            st.subheader(
                "🤖 AI-Generated Policy Answer"
            )

            st.success(
                answer
            )

            # -------------------------------------------------
            # SOURCES
            # -------------------------------------------------

            st.subheader(
                "📚 Policy Sources & References"
            )

            st.caption(
                "The following policy sections were retrieved "
                "from the knowledge base and provided to the AI model as context."
            )

            for i, document in enumerate(
                results
            ):

                page_number = (
                    document.metadata.get(
                        "page",
                        "Unknown"
                    )
                )

                if isinstance(
                    page_number,
                    int
                ):

                    display_page = (
                        page_number + 1
                    )

                else:

                    display_page = (
                        page_number
                    )

                st.write(
                    f"**Source {i + 1} — Policy Page {display_page}**"
                )

                with st.expander(
                    "📄 View Retrieved Policy Content"
                ):

                    st.write(
                        document.page_content
                    )


# =========================================================
# FOOTER / DEMO INFORMATION
# =========================================================

st.divider()

st.caption(
    "Enterprise HR Policy AI Assistant • "
    "Retrieval-Augmented Generation (RAG) • "
    "HuggingFace Embeddings • ChromaDB • Ollama"
)