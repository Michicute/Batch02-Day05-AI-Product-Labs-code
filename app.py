import streamlit as st

from src.rag_agent import RagAgent


st.set_page_config(page_title="Medicine Q&A RAG", page_icon="M", layout="wide")


@st.cache_resource(show_spinner="Building retrieval index...")
def get_agent() -> RagAgent:
    return RagAgent()


agent = get_agent()

st.title("Medicine Q&A RAG")
st.caption("Local retrieval over data_clean.csv and medicine_clean.csv")

with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Retrieved records", min_value=1, max_value=10, value=5)
    use_llm = st.toggle("Use OpenAI answer generation", value=False)
    st.caption("Turn on only when OPENAI_API_KEY is configured.")

question = st.text_input(
    "Ask a question",
    placeholder="Example: What are the side effects of Augmentin 625 Duo Tablet?",
)

if question:
    with st.spinner("Retrieving relevant records..."):
        try:
            result = agent.answer(question, top_k=top_k, use_llm=use_llm)
        except Exception as exc:
            st.error(f"Could not generate an answer: {exc}")
            st.stop()

    st.subheader("Answer")
    st.write(result["answer"])

    st.subheader("Sources")
    for idx, source in enumerate(result["sources"], start=1):
        with st.expander(
            f"{idx}. {source['title']} · {source['source']} · score {source['score']}"
        ):
            st.json(source["metadata"])
else:
    st.info("Ask about a disease, symptom, treatment, medicine, composition, side effect, or manufacturer.")
