import os
import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

# 1. Configuration & Setup
CHROMA_DIR = "./chroma_db"
CHROMA_COLLECTION_NAME = "plantmind_knowledge"

st.set_page_config(page_title="PlantMind — Industrial Knowledge Assistant", page_icon="🌱", layout="wide")

@st.cache_resource
def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
    return collection

@st.cache_resource
def get_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

collection = get_chroma_collection()
model = get_embedding_model()

# 2. Hybrid Retrieve Function
def hybrid_retrieve(query, n_manual=5, n_workorder=3):
    try:
        query_embedding = model.encode([query], convert_to_numpy=True).tolist()[0]
        
        # Manual query
        manual_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_manual,
            where={"source_type": "manual"}
        )
        
        # Work order query
        wo_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_workorder,
            where={"source_type": "work_order"}
        )
        
        results = []
        if manual_results and manual_results.get('documents') and manual_results['documents'][0]:
            for doc, meta in zip(manual_results['documents'][0], manual_results['metadatas'][0]):
                results.append({"text": doc, "metadata": meta})
                
        if wo_results and wo_results.get('documents') and wo_results['documents'][0]:
            for doc, meta in zip(wo_results['documents'][0], wo_results['metadatas'][0]):
                results.append({"text": doc, "metadata": meta})
                
        return results
    except Exception as e:
        st.error(f"Error during retrieval: {e}")
        return []

# 3. Setup Groq Client
groq_api_key = os.environ.get("GROQ_API_KEY")

# 4. Streamlit UI
st.title("PlantMind — Industrial Knowledge Assistant")

if not groq_api_key:
    st.error("GROQ_API_KEY environment variable is not set. Please set it to use the assistant.")
    st.stop()

try:
    groq_client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()

# 6. Sidebar
with st.sidebar:
    st.header("About PlantMind")
    st.write("PlantMind unifies equipment manuals and maintenance history into one searchable knowledge base for field technicians.")
    st.subheader("Knowledge Base Stats")
    try:
        total_chunks = collection.count()
        st.write(f"**Total chunks:** {total_chunks}")
        
        # Try to get breakdown by retrieving all metadatas
        # Note: For very large collections, this might be slow, but works fine for prototyping
        all_data = collection.get(include=["metadatas"])
        manual_count = sum(1 for m in all_data['metadatas'] if m.get('source_type') == 'manual')
        wo_count = sum(1 for m in all_data['metadatas'] if m.get('source_type') == 'work_order')
        
        st.write(f"- Manuals: {manual_count}")
        st.write(f"- Work Orders: {wo_count}")
    except Exception as e:
        st.write("Stats unavailable at the moment.")

# 5. Chat History Setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources used"):
                for src in message["sources"]:
                    st.markdown(src)

# Chat Input & Processing
if prompt := st.chat_input("Ask about equipment maintenance or manuals..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Process Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("Searching PlantMind knowledge base..."):
            retrieved = hybrid_retrieve(prompt)
        
        if not retrieved:
            st.warning("No relevant information found in the knowledge base.")
            response = "I couldn't find any relevant information to answer your question."
            sources_to_show = []
            message_placeholder.markdown(response)
        else:
            # Build Context string
            context_texts = []
            sources_to_show = []
            
            for i, item in enumerate(retrieved, 1):
                text = item["text"]
                meta = item["metadata"]
                
                src_type = meta.get("source_type", "unknown")
                if src_type == "manual":
                    src_str = f"Manual: {meta.get('source_file')} (Page {meta.get('page_number')})"
                else:
                    src_str = f"Work Order: {meta.get('source_file')} (Asset: {meta.get('asset_id')})"
                
                context_texts.append(f"--- Chunk {i} ({src_str}) ---\n{text}\n")
                
                # Format for expander UI
                asset_id = meta.get('asset_id') or "N/A"
                page_num = meta.get('page_number') or "N/A"
                sources_to_show.append(f"- **{src_type}**: `{meta.get('source_file')}` | Asset: {asset_id} | Page: {page_num}")
            
            context_block = "\n".join(context_texts)
            
            system_prompt = (
                "You are an industrial maintenance assistant. "
                "Answer the user's question ONLY based on the provided context chunks. "
                "If the context does not contain the answer, clearly state 'I don't have enough information to answer that.' "
                "Always cite which source (e.g., manual filename + page, or work order ID) each piece of information came from."
            )
            
            user_msg = f"Context information is below:\n\n{context_block}\n\nUser Question: {prompt}"
            
            messages_for_llm = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
            
            try:
                with st.spinner("Generating answer..."):
                    completion = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages_for_llm,
                        temperature=0.2,
                    )
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                
                with st.expander("Sources used"):
                    for src in sources_to_show:
                        st.markdown(src)
                        
            except Exception as e:
                response = f"Error calling Groq API: {e}"
                message_placeholder.error(response)
                sources_to_show = []

    # Save to history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "sources": sources_to_show
    })
