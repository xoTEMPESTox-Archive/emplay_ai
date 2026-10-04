#!/usr/bin/env bash
# ==============================================================================
# RFP Intelligence Platform — One-Click Setup & Launch Script
# ==============================================================================
set -e

# Change directory to script directory (deliverables/source_code)
cd "$(dirname "$0")"

echo "================================================================="
echo "  RFP Intelligence Platform — Initializing Environment"
echo "================================================================="

# 1. Locate or create Python virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Creating Python virtual environment in $VENV_DIR..."
    if command -v python3 &>/dev/null; then
        python3 -m venv "$VENV_DIR"
    elif command -v python &>/dev/null; then
        python -m venv "$VENV_DIR"
    else
        echo "[!] Error: Python is not installed or not in PATH."
        exit 1
    fi
else
    echo "[✓] Existing virtual environment found: $VENV_DIR"
fi

# 2. Activate virtual environment (handles Linux/macOS and Windows Git Bash)
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    echo "[!] Error: Cannot find virtual environment activation script."
    exit 1
fi

# 3. Install packages if not already installed
if python -c "import rfp_intelligence, streamlit" &>/dev/null; then
    echo "[✓] Dependencies already installed. Skipping package installation."
else
    echo "[+] Installing project dependencies and Streamlit..."
    pip install --upgrade pip
    pip install -e .
    pip install streamlit
fi

# 4. Initialize .env if missing
if [ ! -f ".env" ] && [ ! -f "../../.env" ]; then
    echo "[+] Creating .env from .env.example..."
    cp .env.example .env
    echo "[!] Note: Check .env to configure your preferred LLM provider and API keys."
fi

# 5. Trap signals to cleanly stop child processes on exit
cleanup() {
    echo ""
    echo "[*] Shutting down services..."
    if [ -n "$API_PID" ]; then kill "$API_PID" 2>/dev/null || true; fi
    if [ -n "$WEB_PID" ]; then kill "$WEB_PID" 2>/dev/null || true; fi
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 6. Launch FastAPI Backend
echo "[+] Starting FastAPI Backend on port 8000..."
python -m rfp_intelligence.cli serve --host 127.0.0.1 --port 8000 &
API_PID=$!

# Brief pause to allow backend initialization
sleep 2

# 7. Launch Streamlit Web UI
echo "[+] Starting Streamlit Web UI on port 8501..."
streamlit run web_ui.py --server.port 8501 --server.address 127.0.0.1 --server.headless true &
WEB_PID=$!

sleep 2

# 8. Display active endpoints and instructions
echo ""
echo "================================================================="
echo "  🚀 All Services Running Successfully!"
echo "================================================================="
echo "  💬 Streamlit Web UI:    http://localhost:8501"
echo "  📡 REST API Health:     http://localhost:8000/health"
echo "  📖 Swagger API Docs:    http://localhost:8000/docs"
echo "================================================================="
echo "  Press Ctrl+C in this terminal to stop both servers."
echo "================================================================="

# Keep script running to monitor processes
wait
