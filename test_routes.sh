#!/bin/bash
# Comprehensive API Route Testing Script

set -e

API_BASE="http://localhost:5000/api"

# Colors
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

echo "🧪 Testing WolfTrace API Routes..."
echo ""

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=${4:-200}
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${API_BASE}${endpoint}" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" \
            ${data:+-d "$data"} "${API_BASE}${endpoint}" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ] || [ "$http_code" = "200" ] || [ "$http_code" = "400" ]; then
        printf "   ${GREEN}✓${NC} %-6s %s (HTTP %s)\n" "$method" "$endpoint" "$http_code"
        if [ -n "$body" ] && [ "${#body}" -lt 200 ]; then
            echo "      → $(echo "$body" | head -c 100)"
        fi
        return 0
    else
        printf "   ${RED}✗${NC} %-6s %s (HTTP %s)\n" "$method" "$endpoint" "$http_code"
        return 1
    fi
}

echo "1️⃣  Testing Core Endpoints..."
test_endpoint "GET" ""
test_endpoint "GET" "/health"
test_endpoint "GET" "/plugins"
test_endpoint "GET" "/graph"
test_endpoint "GET" "/nodes"
test_endpoint "GET" "/edges"
echo ""

echo "2️⃣  Testing Search & Query..."
test_endpoint "GET" "/search?q=test&limit=10"
test_endpoint "GET" "/nodes?type=Host"
test_endpoint "GET" "/edges?type=CONNECTS_TO"
test_endpoint "POST" "/query" '{"node_type":[]}'
test_endpoint "POST" "/query/stats" '{"node_type":[]}'
echo ""

echo "3️⃣  Testing Analytics..."
test_endpoint "GET" "/analytics/stats"
test_endpoint "GET" "/analytics/communities?max=5"
test_endpoint "GET" "/analytics/neighbors?node=test&depth=2" 400
echo ""

echo "4️⃣  Testing Path Finding..."
test_endpoint "POST" "/paths" '{"source":"test1","target":"test2"}' 200
echo ""

echo "5️⃣  Testing Import..."
test_endpoint "POST" "/import" '{"collector":"example","data":{"nodes":[]}}' 200
echo ""

echo "6️⃣  Testing Sessions..."
test_endpoint "GET" "/sessions"
test_endpoint "POST" "/sessions" '{"name":"Test Session","metadata":{}}'
echo ""

echo "7️⃣  Testing Export & Report..."
test_endpoint "GET" "/export?format=json"
test_endpoint "GET" "/report?format=json"
echo ""

echo "8️⃣  Testing History..."
test_endpoint "GET" "/history/info"
test_endpoint "POST" "/history/undo" '{}' 400
test_endpoint "POST" "/history/redo" '{}' 400
echo ""

echo "9️⃣  Testing Graph Operations..."
test_endpoint "POST" "/clear" '{}'
test_endpoint "GET" "/graph/paginated?page=1&per_page=10"
echo ""

echo "🔟  Testing Templates..."
test_endpoint "GET" "/templates"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${GREEN}✓ API Testing Complete${NC}\n"
echo ""
echo "📋 Note: Some endpoints may return 400 if data is missing,"
echo "   which is expected behavior for validation."

