#!/bin/sh
set -eu

PROJECT_NAME="${1:-onyx-compose-probe-5cha60}"
API_CONTAINER="${PROJECT_NAME}-api_server-1"
BACKGROUND_CONTAINER="${PROJECT_NAME}-background-1"
CODE_INTERPRETER_CONTAINER="${PROJECT_NAME}-code-interpreter-1"
CACHE_CONTAINER="${PROJECT_NAME}-cache-1"
NGINX_CONTAINER="${PROJECT_NAME}-nginx-1"

require_container() {
    container_name="$1"
    docker inspect "$container_name" >/dev/null 2>&1 || {
        echo "ERROR: container not found: $container_name" >&2
        exit 1
    }
}

run_in() {
    container_name="$1"
    command_string="$2"
    docker exec "$container_name" sh -lc "$command_string"
}

check_tool() {
    container_name="$1"
    tool_name="$2"
    echo "Checking ${tool_name} in ${container_name}"
    docker exec "$container_name" which "$tool_name" >/dev/null 2>&1
}

check_http_contains() {
    container_name="$1"
    url="$2"
    expected_text="$3"
    echo "Checking ${url} in ${container_name}"
    docker exec "$container_name" python -c "import sys, urllib.request; body = urllib.request.urlopen('${url}', timeout=20).read().decode(); print(body); sys.exit(0 if '${expected_text}' in body else 1)"
}

check_host_sysctl_eq() {
    sysctl_key="$1"
    expected_value="$2"
    echo "Checking host sysctl ${sysctl_key}"
    actual_value="$(sysctl -n "$sysctl_key" 2>/dev/null || true)"
    if [ "$actual_value" != "$expected_value" ]; then
        echo "ERROR: host sysctl ${sysctl_key}=${actual_value:-<unset>} expected ${expected_value}" >&2
        exit 1
    fi
}

check_host_sysctl_eq vm.overcommit_memory 1

for container_name in "$API_CONTAINER" "$BACKGROUND_CONTAINER" "$CODE_INTERPRETER_CONTAINER" "$CACHE_CONTAINER" "$NGINX_CONTAINER"; do
    require_container "$container_name"
done

echo "Checking Craft runtime tools in api_server"
for tool_name in curl opencode git jq rg fd sqlite3 ffmpeg convert pandoc pdftotext tesseract; do
    check_tool "$API_CONTAINER" "$tool_name"
done

echo "Checking Craft runtime tools in background"
for tool_name in curl opencode git jq rg fd sqlite3 ffmpeg convert pandoc pdftotext tesseract; do
    check_tool "$BACKGROUND_CONTAINER" "$tool_name"
done

echo "Checking cache health"
run_in "$CACHE_CONTAINER" "redis-cli ping | grep -qx PONG"

echo "Checking nginx proxy health"
run_in "$NGINX_CONTAINER" "wget -q --spider http://127.0.0.1/"
run_in "$NGINX_CONTAINER" 'body=$(wget -q -O - http://127.0.0.1/api/health); printf "%s\n" "$body"; printf "%s" "$body" | grep -q "\"success\":true"'

echo "Checking UNSTRUCTURED_API_URL wiring"
run_in "$API_CONTAINER" 'printenv UNSTRUCTURED_API_URL | grep -qx "http://unstructured_api:8000"'
run_in "$BACKGROUND_CONTAINER" 'printenv UNSTRUCTURED_API_URL | grep -qx "http://unstructured_api:8000"'
run_in "$API_CONTAINER" "getent hosts unstructured_api >/dev/null"
run_in "$BACKGROUND_CONTAINER" "getent hosts unstructured_api >/dev/null"

echo "Checking health endpoints"
check_http_contains "$API_CONTAINER" "http://localhost:8080/health" '"success":true'
check_http_contains "$CODE_INTERPRETER_CONTAINER" "http://localhost:8000/health" '"status":"ok"'

echo "Craft smoke test passed for project ${PROJECT_NAME}"
