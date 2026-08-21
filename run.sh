#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  Enterprise Multimodal RAG Assistant — one-command startup
# ─────────────────────────────────────────────────────────────────────────────
#  Usage:
#    ./run.sh            # install deps (if missing) and start backend + frontend
#    ./run.sh --no-install
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  🏢 Enterprise Multimodal RAG Assistant — Startup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. Virtual environment
if [ ! -d ".venv" ]; then
  echo -e "${YELLOW}→ Creating virtual environment (.venv)...${NC}"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 2. Dependencies
if [ "${1:-}" != "--no-install" ]; then
  echo -e "${YELLOW}→ Installing dependencies...${NC}"
  pip install -q --upgrade pip
  pip install -q -r requirements.txt
fi

# 3. Environment file
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}→ Creating .env from .env.example (set GOOGLE_API_KEY / TOKEN_SECRET as needed)...${NC}"
  cp .env.example .env
fi

# 4. Dummy documents
if [ ! "$(ls -A data/documents 2>/dev/null)" ]; then
  echo -e "${YELLOW}→ Generating dummy enterprise documents...${NC}"
  python scripts/generate_dummy_documents.py
fi

# 5. Run backend & frontend
echo -e "${GREEN}→ Starting FastAPI backend on http://localhost:8000 ...${NC}"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo -e "${GREEN}→ Starting Streamlit frontend on http://localhost:8501 ...${NC}"
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &

FRONTEND_PID=$!

trap "echo; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Backend  →  http://localhost:8000   (docs: /docs)${NC}"
echo -e "${GREEN}  ✅ Frontend →  http://localhost:8501${NC}"
echo -e "${GREEN}  Demo logins: emp001/Emp@123 · hr001/HR@123 · fin001/Fin@123 · admin001/Admin@123${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Press Ctrl+C to stop both servers."

wait