#!/bin/bash

# launch script for llm-vc-dungeon frontend and backend

set -e

# colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # no color

# get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_DIR="$SCRIPT_DIR/src/api"
SVELTE_DIR="$SCRIPT_DIR/src/svelte"
VENV_DIR="$API_DIR/venv"

echo -e "${GREEN}starting llm-vc-dungeon...${NC}"

# check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}virtual environment not found at $VENV_DIR${NC}"
    echo "creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}virtual environment created${NC}"
fi

# activate venv
echo -e "${GREEN}activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# install/update backend dependencies if needed
if [ -f "$API_DIR/requirements.txt" ]; then
    echo -e "${GREEN}installing backend dependencies...${NC}"
    pip install -q -r "$API_DIR/requirements.txt"
fi

# start backend in background
echo -e "${GREEN}starting backend server...${NC}"
cd "$API_DIR"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!

# give backend a moment to start
sleep 2

# start frontend in background
echo -e "${GREEN}starting frontend server...${NC}"
cd "$SVELTE_DIR"
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!

# give frontend a moment to start
sleep 2

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}both servers are running!${NC}"
echo -e "${GREEN}backend: http://localhost:8000${NC}"
echo -e "${GREEN}frontend: http://localhost:5173${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}press ctrl+c to stop all servers${NC}"

# trap ctrl+c and kill both processes
trap "echo -e '\n${YELLOW}stopping servers...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; wait; exit 0" INT TERM

# wait for both processes
wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
