#!/bin/bash
# scripts/check.sh - 品質チェックスクリプト
#
# Usage:
#   ./scripts/check.sh          # 全チェック実行
#   ./scripts/check.sh lint     # Lint のみ
#   ./scripts/check.sh format   # Format Check のみ
#   ./scripts/check.sh type     # Type Check のみ
#   ./scripts/check.sh test     # Test のみ
#   ./scripts/check.sh cov      # Coverage 付きテスト

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

run_lint() {
    print_header "🔍 Ruff (Lint)"
    poetry run ruff check .
    echo -e "${GREEN}✓ Lint passed${NC}"
}

run_format() {
    print_header "🎨 Ruff (Format Check)"
    poetry run ruff format --check .
    echo -e "${GREEN}✓ Format check passed${NC}"
}

run_type() {
    print_header "📝 Mypy (Type Check)"
    poetry run mypy src/
    echo -e "${GREEN}✓ Type check passed${NC}"
}

run_test() {
    print_header "🧪 Pytest"
    poetry run pytest -q
    echo -e "${GREEN}✓ Tests passed${NC}"
}

run_coverage() {
    print_header "📊 Coverage"
    poetry run pytest --cov=src --cov-report=term-missing --cov-fail-under=90 -q
    echo -e "${GREEN}✓ Coverage check passed (≥90%)${NC}"
}

run_all() {
    run_lint
    run_format
    run_type
    run_coverage
}

print_success() {
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ $1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

case "${1:-all}" in
    lint)
        run_lint
        print_success "Lint check completed!"
        ;;
    format)
        run_format
        print_success "Format check completed!"
        ;;
    type)
        run_type
        print_success "Type check completed!"
        ;;
    test)
        run_test
        print_success "Tests completed!"
        ;;
    cov)
        run_coverage
        print_success "Coverage check completed!"
        ;;
    all)
        run_all
        print_success "All checks completed successfully!"
        ;;
    *)
        echo "Usage: $0 {lint|format|type|test|cov|all}"
        exit 1
        ;;
esac
