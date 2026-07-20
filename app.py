import os
import streamlit as st
import chromadb
import pandas as pd
import re
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

# 2.5 Failure Pattern Analysis
@st.cache_data
def load_work_orders():
    try:
        return pd.read_csv("data/synthetic_logs/all_work_orders.csv")
    except Exception as e:
        st.error(f"Could not load work order data: {e}")
        return pd.DataFrame()

df_work_orders = load_work_orders()

def is_pattern_query(query: str) -> bool:
    keywords = [
        "pattern", "recurring", "most common", "trend", 
        "which equipment", "how many times", "frequency", 
        "top failures", "worst performing", "most frequent"
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)

def analyze_failure_patterns(query: str, df: pd.DataFrame) -> str:
    if df.empty:
        return "No work order data available for analysis."
    
    query_lower = query.lower()
    summary = ["### 📊 Pattern Analysis\n"]
    
    asset_match = re.search(r'\b([A-Z]+-\d+)\b', query, re.IGNORECASE)
    mentioned_asset = None
    if asset_match:
        mentioned_asset = asset_match.group(1).upper()
    else:
        for asset in df['asset_id'].dropna().unique():
            if str(asset).lower() in query_lower:
                mentioned_asset = str(asset)
                break

    if mentioned_asset and mentioned_asset in df['asset_id'].values:
        summary.append(f"**Asset History Summary for {mentioned_asset}**")
        asset_df = df[df['asset_id'] == mentioned_asset]
        summary.append(f"- **Total Work Orders**: {len(asset_df)}")
        if 'failure_mode' in df.columns:
            top_failures = asset_df['failure_mode'].value_counts().head(3)
            summary.append(f"- **Top Failure Modes**: {', '.join([f'{k} ({v})' for k,v in top_failures.items()])}")
        if 'downtime_hours' in df.columns:
            total_downtime = asset_df['downtime_hours'].sum()
            summary.append(f"- **Total Downtime**: {total_downtime:.1f} hours")
        return "\n".join(summary)
        
    if "downtime" in query_lower or "worst" in query_lower:
        if 'failure_mode' in df.columns and 'downtime_hours' in df.columns:
            avg_downtime = df.groupby('failure_mode')['downtime_hours'].mean().sort_values(ascending=False)
            summary.append("**Average Downtime by Failure Mode (Top 5)**")
            for k, v in avg_downtime.head(5).items():
                summary.append(f"- {k}: {v:.1f} hours")
            return "\n".join(summary)
            
    if "equipment" in query_lower or "asset" in query_lower:
        if 'asset_id' in df.columns:
            top_assets = df['asset_id'].value_counts().head(5)
            summary.append("**Assets with the Most Work Orders (Top 5)**")
            for k, v in top_assets.items():
                summary.append(f"- {k}: {v} incidents")
            return "\n".join(summary)
            
    if "type" in query_lower and "failure" in query_lower:
        if 'asset_type' in df.columns and 'failure_mode' in df.columns:
            combo = df.groupby(['asset_type', 'failure_mode']).size().reset_index(name='count')
            combo = combo.sort_values('count', ascending=False).head(5)
            summary.append("**Most Frequent Failure Modes by Asset Type (Top 5)**")
            for _, row in combo.iterrows():
                summary.append(f"- {row['asset_type']} - {row['failure_mode']}: {row['count']} incidents")
            return "\n".join(summary)

    # Default: Most common failure modes
    if 'failure_mode' in df.columns:
        top_failures = df['failure_mode'].value_counts().head(5)
        summary.append("**Most Common Failure Modes Overall (Top 5)**")
        for k, v in top_failures.items():
            summary.append(f"- {k}: {v} incidents")
        return "\n".join(summary)

    return "Could not determine a specific pattern analysis for your query based on the available data."

# 2.6 Root Cause Analysis (RCA) Mode
def is_rca_query(query: str) -> bool:
    keywords = [
        "why is", "what's causing", "what is causing",
        "troubleshoot", "diagnose",
        "vibrating", "making noise", "not working",
        "failing", "leaking", "overheating",
        "won't start", "wont start", "malfunction",
        "issue with", "problem with"
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)

def build_rca_prompt(query: str, retrieved_chunks: list) -> tuple[str, str]:
    """Returns (system_prompt, user_msg) for an RCA-structured Groq call."""
    context_texts = []
    for i, item in enumerate(retrieved_chunks, 1):
        text = item["text"]
        meta = item["metadata"]
        src_type = meta.get("source_type", "unknown")
        if src_type == "manual":
            src_str = f"Manual: {meta.get('source_file')} (Page {meta.get('page_number')})"
        else:
            src_str = f"Work Order: {meta.get('source_file')} (Asset: {meta.get('asset_id')})"
        context_texts.append(f"--- Chunk {i} ({src_str}) ---\n{text}\n")
    context_block = "\n".join(context_texts)

    system_prompt = (
        "You are an expert industrial maintenance engineer performing Root Cause Analysis (RCA). "
        "You MUST use ONLY the context chunks provided below — do not draw on external knowledge. "
        "If the context does not contain enough information to fill any section confidently, explicitly state that in that section. "
        "Structure your entire response using these exact markdown headings and no others:\n\n"
        "## Likely Root Cause(s)\n"
        "List 1–3 most probable causes ranked by likelihood, based strictly on the provided context.\n\n"
        "## Supporting Evidence\n"
        "Reference specific work order IDs and manual page numbers from the context that support each cause.\n\n"
        "## Recommended Action\n"
        "Provide concrete next steps a field technician should take, drawn only from the retrieved content.\n\n"
        "## Confidence Level\n"
        "State High / Medium / Low and explain briefly — e.g. \"High: 4 similar past incidents found with matching root cause\" "
        "or \"Low: limited historical data, primarily based on general manual guidance\"."
    )

    user_msg = (
        f"Context information is below:\n\n{context_block}\n\n"
        f"Symptom / Problem reported by technician: {query}\n\n"
        "Perform a Root Cause Analysis using ONLY the context above."
    )
    return system_prompt, user_msg

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
        
    st.markdown("---")
    st.subheader("💡 Pro Tips")
    st.write("**Patterns:** *'What are the most common failure modes?'* or *'Which equipment fails most often?'*")
    st.write("**Troubleshooting:** *'Why is my pump vibrating?'* or *'What\'s causing the compressor to overheat?'*")

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
        
        if is_pattern_query(prompt):
            with st.spinner("Analyzing failure patterns..."):
                response = analyze_failure_patterns(prompt, df_work_orders)
            message_placeholder.markdown(response)
            sources_to_show = []
        elif is_rca_query(prompt):
            with st.spinner("🔧 Running Root Cause Analysis..."):
                retrieved = hybrid_retrieve(prompt)
            if not retrieved:
                st.warning("No relevant information found in the knowledge base for RCA.")
                response = "I couldn't find enough context to perform a root cause analysis."
                sources_to_show = []
                message_placeholder.markdown(response)
            else:
                sources_to_show = []
                for item in retrieved:
                    meta = item["metadata"]
                    src_type = meta.get("source_type", "unknown")
                    asset_id = meta.get('asset_id') or "N/A"
                    page_num = meta.get('page_number') or "N/A"
                    sources_to_show.append(
                        f"- **{src_type}**: `{meta.get('source_file')}` | Asset: {asset_id} | Page: {page_num}"
                    )
                rca_system_prompt, rca_user_msg = build_rca_prompt(prompt, retrieved)
                messages_for_llm = [
                    {"role": "system", "content": rca_system_prompt},
                    {"role": "user", "content": rca_user_msg}
                ]
                try:
                    with st.spinner("Generating root cause analysis..."):
                        completion = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages_for_llm,
                            temperature=0.1,
                        )
                    response = completion.choices[0].message.content
                    st.markdown("**🔧 Root Cause Analysis**")
                    message_placeholder.markdown(response)
                    with st.expander("Sources used"):
                        for src in sources_to_show:
                            st.markdown(src)
                except Exception as e:
                    response = f"Error calling Groq API: {e}"
                    message_placeholder.error(response)
                    sources_to_show = []
        else:
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
