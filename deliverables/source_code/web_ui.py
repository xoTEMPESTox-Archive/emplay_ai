"""
Streamlit Web UI for RFP Intelligence Platform.
Full Agentic RAG chat interface with Live Traces, 20-Field Extractions,
Bid Comparison, Retrieval Benchmarks, and Multi-Agent Architecture Showcase.
"""

import json
import os
from pathlib import Path
import time
import streamlit as st

from rfp_intelligence.config import settings
from rfp_intelligence.agents.tools import AgentTools

# ------------------------------------------------------------------------------
# Streamlit Cloud Secrets Injection (if available)
# ------------------------------------------------------------------------------
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

st.set_page_config(
    page_title="RFP Intelligence Platform",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Repository Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DELIVERABLES_DIR = REPO_ROOT / "deliverables"
OUTPUTS_DIR = DELIVERABLES_DIR / "outputs"

# ------------------------------------------------------------------------------
# Sidebar: Model, API Settings & Quick Local Setup
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ Model & API Settings")

PROVIDER_MODELS = {
    "Google Gemini (Recommended)": "gemini/gemini-2.5-flash",
    "Groq (Fast Cloud)": "groq/openai/gpt-oss-120b",
    "OpenAI": "openai/gpt-4o-mini",
    "Anthropic Claude": "anthropic/claude-3-5-sonnet-20241022",
    "Local Ollama (Offline)": "ollama/qwen2.5:3b",
}

selected_provider = st.sidebar.selectbox("LLM Provider & Model", list(PROVIDER_MODELS.keys()), index=0)
active_model = PROVIDER_MODELS[selected_provider]

user_api_key = st.sidebar.text_input(
    "Custom API Key (Optional)",
    type="password",
    help="Stored only in your current browser session state. If left blank, uses system environment / demo fallback.",
    placeholder="Paste your API key here...",
)

st.sidebar.info(
    "ℹ️ **Evaluator Demo Notice:**\n\n"
    "A free shared Groq API key is pre-configured for evaluation, but is rate-limited and expires on **October 12, 2026** (7-day duration).\n\n"
    "If you encounter a rate limit or quota notice, simply paste your personal Gemini, OpenAI, or Groq API key above!"
)

st.sidebar.divider()

with st.sidebar.expander("💻 One-Click Local Setup", expanded=False):
    os_choice = st.radio("Operating System", ["macOS / Linux", "Windows (PowerShell)"], horizontal=True)
    if os_choice == "macOS / Linux":
        st.code(
            "git clone https://github.com/xoTEMPESTox-Archive/emplay_ai.git && cd emplay_ai/deliverables/source_code && bash run.sh",
            language="bash",
        )
    else:
        st.code(
            "git clone https://github.com/xoTEMPESTox-Archive/emplay_ai.git; cd emplay_ai/deliverables/source_code; powershell -ExecutionPolicy Bypass -File .\\run.ps1",
            language="powershell",
        )
    st.caption("Bootstraps virtual env, installs dependencies, starts FastAPI & Streamlit.")

# ------------------------------------------------------------------------------
# Top Header
# ------------------------------------------------------------------------------
st.title("📋 RFP Intelligence Platform: Hybrid RAG & Multi-Agent System")
st.caption(f"Active Model: `{active_model}` | Advanced: Multi-Query Decomposition, Balanced Cross-Bid Retrieval & Listwise Reranking")

# Initialize cached AgentTools
@st.cache_resource
def get_agent_tools():
    return AgentTools()

agent_tools = get_agent_tools()

# Tabs for Deliverables & Interaction
tab_chat, tab_extractions, tab_comparison, tab_eval, tab_arch = st.tabs([
    "💬 RFP Intelligence Chat & Traces",
    "📊 Structured Extractions (20 Fields)",
    "⚖️ Bid Comparison & Go/No-Go",
    "📈 Retrieval Benchmark",
    "🏗️ Multi-Agent Architecture",
])

# ==============================================================================
# TAB 1: Chat Interface & Live Agentic Traces
# ==============================================================================
with tab_chat:
    available_bids = ["All Bids"] + (agent_tools.engine.get_indexed_bids() or ["Bid1", "Bid2"])
    col_scope, col_hint = st.columns([1, 3])
    with col_scope:
        bid_filter = st.selectbox("Target Bid Scope", available_bids, index=0)
    with col_hint:
        st.info("💡 Try asking: *'What is the submission deadline for Bid1 after all addendums?'* or *'What are the processor, RAM, and display specs for Bid1 vs Bid2?'*")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your RFP Intelligence assistant powered by Multi-Query RAG and Agentic Reconciliation. Ask any question about **Bid1** (Dallas ISD Student and Staff Computing Devices) or **Bid2** (State of Maryland Dell laptops), and I will provide answers with exact source citations.",
                "citations": [],
                "sub_queries": [],
                "traces": {},
            }
        ]

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sub_queries"):
                with st.expander("🔍 Query Decomposition Steps", expanded=False):
                    st.markdown("**Sub-Queries Executed:**")
                    for sq in msg["sub_queries"]:
                        st.markdown(f"- `{sq}`")
            if msg.get("citations"):
                with st.expander("📚 Source Evidence & Passages", expanded=False):
                    for cit in msg["citations"]:
                        bid_prefix = f"[{cit['bid']}] " if cit.get("bid") else ""
                        st.markdown(f"- **{bid_prefix}{cit['file']}** (Page {cit['page']}):\n  > *\"{cit['snippet']}\"*")

    # User chat input
    if prompt := st.chat_input("Ask a question about the RFP documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "citations": [], "sub_queries": [], "traces": {}})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            target_bid = None if bid_filter == "All Bids" else bid_filter
            effective_key = user_api_key.strip() if user_api_key else None
            if not effective_key and "groq" in active_model:
                effective_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")

            try:
                start_exec = time.time()
                with st.status("Executing Agentic RAG Pipeline...", expanded=False) as status:
                    st.write("🔄 Decomposing query into targeted sub-queries...")
                    rag_result = agent_tools.run_agentic_rag(
                        prompt,
                        bid_id=target_bid,
                        model=active_model,
                        api_key=effective_key,
                    )
                    latency = round(time.time() - start_exec, 2)
                    st.write(f"🔍 **Sub-Queries Generated:** `{', '.join(rag_result['sub_queries'])}`")
                    st.write(f"🎯 **Target Bid Scope:** `{rag_result['target_bid'] or 'Cross-Bid'}`")
                    st.write(f"📄 **Evidentiary Passages Selected:** {len(rag_result['passages'])} passages")
                    st.write(f"⏱️ **Total Execution Time:** `{latency}s`")
                    status.update(label=f"RAG Retrieval Complete ({latency}s)!", state="complete")

                full_response = rag_result["answer"]
                citations_data = rag_result["citations"]
                sub_queries = rag_result["sub_queries"]

                # Stream response word-by-word
                def response_generator():
                    words = full_response.split(" ")
                    for i, word in enumerate(words):
                        yield word + (" " if i < len(words) - 1 else "")
                        time.sleep(0.01)

                st.write_stream(response_generator())

                # Render inspection expanders
                if sub_queries:
                    with st.expander("🔍 Query Decomposition Steps", expanded=False):
                        st.markdown("**Sub-Queries Executed:**")
                        for sq in sub_queries:
                            st.markdown(f"- `{sq}`")

                if citations_data:
                    with st.expander("📚 Source Evidence & Passages", expanded=False):
                        for cit in citations_data:
                            bid_prefix = f"[{cit['bid']}] " if cit.get("bid") else ""
                            st.markdown(f"- **{bid_prefix}{cit['file']}** (Page {cit['page']}):\n  > *\"{cit['snippet']}\"*")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "citations": citations_data,
                    "sub_queries": sub_queries,
                    "traces": {"latency_sec": latency, "model": active_model},
                })

            except Exception as e:
                err_str = str(e)
                if "RATE_LIMIT" in err_str:
                    st.error(
                        "⚠️ **API Rate Limit / Quota Exceeded**\n\n"
                        "The current API key has hit its rate limit or token quota.\n\n"
                        "👉 **Resolution:** Please select your provider and paste your personal API key (e.g. Google Gemini, Groq, or OpenAI) in the **⚙️ Model & API Settings** panel on the left sidebar to continue immediately."
                    )
                elif "AUTH_ERROR" in err_str:
                    st.error(
                        "🔑 **API Authentication Failed**\n\n"
                        "The provided API key is invalid or unauthorized.\n\n"
                        "👉 **Resolution:** Please verify your API key in the **⚙️ Model & API Settings** panel on the left sidebar."
                    )
                else:
                    st.error(f"❌ An error occurred during processing: {e}")

# ==============================================================================
# TAB 2: Structured Extractions (20 Fields)
# ==============================================================================
with tab_extractions:
    st.subheader("Structured Information Extraction (20 Mandatory Fields)")
    st.caption("Produced by LangGraph Multi-Agent Orchestration with Addendum Reconciliation and Validator Critic verification.")

    bid_select = st.selectbox("Select Bid Record", ["Bid1 (Dallas ISD Computing Devices)", "Bid2 (State of Maryland Dell Laptops)"])
    selected_bid_file = "Bid1.json" if "Bid1" in bid_select else "Bid2.json"
    bid_json_path = OUTPUTS_DIR / selected_bid_file

    if bid_json_path.exists():
        with open(bid_json_path, "r", encoding="utf-8") as f:
            bid_data = json.load(f)

        fields = bid_data.get("fields", {})
        val_summary = bid_data.get("validation", {})

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Fields", len(fields))
        m2.metric("Validation Passed", val_summary.get("passed", len(fields)))
        m3.metric("Validation Failed", val_summary.get("failed", 0))
        m4.metric("Not Found in Docs", val_summary.get("not_found", sum(1 for v in fields.values() if v.get("value") is None)))

        table_rows = []
        for field_name, f_data in fields.items():
            val = f_data.get("value")
            val_display = str(val) if val is not None else "*(Not found in documents)*"
            conf = f"{int(f_data.get('confidence', 0.0) * 100)}%"
            sources = f_data.get("sources", [])
            src_str = ", ".join(f"{s.get('file', '')} (p. {s.get('page', 'N/A')})" for s in sources) if sources else "None"
            notes = f_data.get("notes", "")
            table_rows.append({
                "Field Name": field_name,
                "Extracted Value": val_display,
                "Confidence": conf,
                "Source Citation": src_str,
                "Reconciliation / Notes": notes,
            })

        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        with st.expander("📄 View Raw Output JSON", expanded=False):
            st.json(bid_data)
    else:
        st.warning(f"Output file {selected_bid_file} not found in deliverables/outputs. Run `python main.py extract --bid ./Bid1` to generate.")

# ==============================================================================
# TAB 3: Bid Comparison & Go/No-Go Decision
# ==============================================================================
with tab_comparison:
    st.subheader("Multi-Agent Bid Comparison & Automated Go / No-Go Decision")
    comp_file = DELIVERABLES_DIR / "bid_comparison_report.md"
    if comp_file.exists():
        with open(comp_file, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("Bid comparison report not found. Run `python main.py compare` to generate.")

# ==============================================================================
# TAB 4: Retrieval Evaluation Benchmark
# ==============================================================================
with tab_eval:
    st.subheader("Quantitative Retrieval Evaluation Framework (Recall@k & MRR)")
    eval_file = DELIVERABLES_DIR / "retrieval_evaluation_report.md"
    if eval_file.exists():
        with open(eval_file, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("Retrieval evaluation report not found.")

# ==============================================================================
# TAB 5: Multi-Agent Architecture
# ==============================================================================
with tab_arch:
    st.subheader("System Architecture & Multi-Agent Collaboration Flow")
    arch_file = DELIVERABLES_DIR / "architecture_diagram.md"
    if arch_file.exists():
        with open(arch_file, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("Architecture documentation not found.")


