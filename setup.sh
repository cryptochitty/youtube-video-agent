#!/bin/bash
set -e

echo "=== YouTube Video Agent Setup ==="

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: node required"; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || {
  echo "Installing ffmpeg..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get install -y ffmpeg
  elif command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  else
    echo "WARNING: Please install ffmpeg manually: https://ffmpeg.org/download.html"
  fi
}

# Backend setup
echo ""
echo "--- Setting up backend ---"
cd backend

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created backend/.env — edit it to configure your LLM provider"
fi

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Backend dependencies installed."

mkdir -p outputs temp
cd ..

# Frontend setup
echo ""
echo "--- Setting up frontend ---"
cd frontend
npm install --silent
cd ..

echo ""
echo "=== Setup complete! ==="
echo ""
echo "BEFORE STARTING:"
echo "  1. Edit backend/.env and set LLM_PROVIDER"
echo "  2. If using Ollama (default): ollama pull llama3.1"
echo "  3. If using Groq: add your free GROQ_API_KEY from console.groq.com"
echo ""
echo "TO START:"
echo "  Terminal 1 — Backend:"
echo "    cd backend && source venv/bin/activate && python run.py"
echo ""
echo "  Terminal 2 — Frontend:"
echo "    cd frontend && npm run dev"
echo ""
echo "  Open: http://localhost:3000"
