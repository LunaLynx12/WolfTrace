#!/bin/bash
# WolfTrace Application Startup Script

set -e

echo "🚀 Starting WolfTrace Application..."
echo ""

# Get IP address
IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d/ -f1 || echo "localhost")

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Export Bun path
export PATH="$HOME/.bun/bin:$PATH"

# Check if Bun is installed
if ! command -v bun &> /dev/null; then
    echo "${YELLOW}⚠ Bun is not installed. Installing Bun...${NC}"
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
fi

# Check backend dependencies
echo "1️⃣  Checking backend dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "${YELLOW}⚠ Python dependencies not installed.${NC}"
    if command -v pip3 &> /dev/null; then
        echo "   Installing Python dependencies..."
        cd backend && pip3 install --user -r requirements.txt
        cd ..
    else
        echo "${RED}✗ pip3 not found. Please install Python dependencies manually:${NC}"
        echo "   ${YELLOW}cd backend && pip3 install -r requirements.txt${NC}"
        echo ""
        echo "   Or use Docker for the backend:"
        echo "   ${YELLOW}docker compose up bucihound${NC}"
        exit 1
    fi
else
    echo "${GREEN}✓ Backend dependencies OK${NC}"
fi
echo ""

# Start backend
echo "2️⃣  Starting backend..."
if pgrep -f "python.*app.py" > /dev/null; then
    echo "${YELLOW}⚠ Backend already running${NC}"
else
    cd backend && nohup python3 app.py > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend started (PID: $BACKEND_PID)"
    sleep 3
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "${GREEN}✓ Backend is running${NC}"
    else
        echo "${YELLOW}⚠ Backend starting... check logs: tail -f /tmp/backend.log${NC}"
    fi
    cd ..
fi
echo ""

# Install frontend dependencies if needed
echo "3️⃣  Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "   Installing frontend dependencies..."
    cd frontend && bun install
    cd ..
else
    echo "${GREEN}✓ Frontend dependencies OK${NC}"
fi
echo ""

# Start frontend
echo "4️⃣  Starting frontend..."
if pgrep -f "bun.*dev" > /dev/null; then
    echo "${YELLOW}⚠ Frontend already running${NC}"
else
    cd frontend && nohup bun run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend started (PID: $FRONTEND_PID)"
    sleep 5
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "${GREEN}✓ Frontend is running${NC}"
    else
        echo "${YELLOW}⚠ Frontend starting... check logs: tail -f /tmp/frontend.log${NC}"
    fi
    cd ..
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "${GREEN}✓ WolfTrace Application Started!${NC}"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: ${GREEN}http://$IP:3000${NC} or ${GREEN}http://localhost:3000${NC}"
echo "   Backend API: ${GREEN}http://$IP:5000/api${NC} or ${GREEN}http://localhost:5000/api${NC}"
echo ""
echo "📋 Test Commands:"
echo "   ./test_app.sh"
echo "   curl http://localhost:5000/api/health"
echo "   curl http://localhost:5000/api/plugins"
echo ""
echo "📝 Logs:"
echo "   Backend: tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 Stop Services:"
echo "   pkill -f 'python.*app.py'"
echo "   pkill -f 'bun.*dev'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

