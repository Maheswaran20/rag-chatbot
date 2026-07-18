import streamlit as st
import requests

API_URL = "https://rag-chatbot-vctv.onrender.com"

st.set_page_config(page_title="RAG Chatbot", page_icon="🤖")
st.title("🤖 RAG Chatbot")
st.caption("Ask questions about your documents")

with st.sidebar:
    st.header("Controls")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/ask",
                    json={"question": prompt},
                    timeout=60,
                )
                data = resp.json()
                answer = data["answer"]
                if data.get("sources"):
                    answer += "\n\n---\n**Sources:** " + ", ".join(data["sources"])
            except Exception as e:
                answer = f"⚠️ Error: {e}"
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})