#!/bin/bash
# WolfTrace Application Test Script

set -e

# Check if terminal supports colors
if [ -t 1 ] && command -v tput > /dev/null 2>&1; then
    GREEN=$(tput setaf 2)
    RED=$(tput setaf 1)
    YELLOW=$(tput setaf 3)
    NC=$(tput sgr0)
else
    GREEN=''
    RED=''
    YELLOW=''
    NC=''
fi

echo "🔍 Testing WolfTrace Application..."
echo ""

# Get IP address
IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d/ -f1 || echo "localhost")

printf "📡 Server IP: ${GREEN}%s${NC}\n" "$IP"
echo ""

# Test Backend Health
echo "1️⃣  Testing Backend API (http://localhost:5000/api/health)..."
if curl -s --connect-timeout 2 http://localhost:5000/api/health > /dev/null 2>&1; then
    printf "   ${GREEN}✓ Backend is running${NC}\n"
    BACKEND_STATUS=$(curl -s http://localhost:5000/api/health)
    echo "   Response: $BACKEND_STATUS"
else
    printf "   ${RED}✗ Backend is not responding${NC}\n"
    printf "   ${YELLOW}→ Start backend with: cd backend && python3 app.py${NC}\n"
    printf "   ${YELLOW}→ Or use Docker: docker compose up bucihound${NC}\n"
fi
echo ""

# Test Frontend
echo "2️⃣  Testing Frontend (http://localhost:3000)..."
if curl -s --connect-timeout 2 http://localhost:3000 > /dev/null 2>&1; then
    printf "   ${GREEN}✓ Frontend is running${NC}\n"
    echo "   Accessible at: http://$IP:3000"
else
    printf "   ${RED}✗ Frontend is not responding${NC}\n"
    printf "   ${YELLOW}→ Start frontend with: cd frontend && bun run dev${NC}\n"
fi
echo ""

# Test API endpoints
echo "3️⃣  Testing API Endpoints..."
ENDPOINTS=(
    "/api/plugins"
    "/api/graph"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s -f "http://localhost:5000$endpoint" > /dev/null 2>&1; then
        printf "   ${GREEN}✓${NC} %s\n" "$endpoint"
    else
        printf "   ${RED}✗${NC} %s\n" "$endpoint"
    fi
done
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access URLs:"
printf "   Frontend: ${GREEN}http://%s:3000${NC} or ${GREEN}http://localhost:3000${NC}\n" "$IP"
printf "   Backend API: ${GREEN}http://%s:5000/api${NC} or ${GREEN}http://localhost:5000/api${NC}\n" "$IP"
echo ""
echo "📋 Quick Test Commands:"
echo "   curl http://localhost:5000/api/health"
echo "   curl http://localhost:5000/api/plugins"
echo "   curl http://localhost:5000/api/graph"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

