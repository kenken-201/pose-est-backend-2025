#!/bin/bash
# scripts/check.sh - 品質チェックスクリプト
#
# Usage:
#   ./scripts/check.sh        # 全チェック実行
#   ./scripts/check.sh lint   # Lint のみ
#   ./scripts/check.sh type   # Type Check のみ
#   ./scripts/check.sh test   # Test のみ
#   ./scripts/check.sh cov    # Coverage 付きテスト

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
    run_type
    run_coverage
}

case "${1:-all}" in
    lint)
        run_lint
        ;;
    type)
        run_type
        ;;
    test)
        run_test
        ;;
    cov)
        run_coverage
        ;;
    all)
        run_all
        ;;
    *)
        echo "Usage: $0 {lint|type|test|cov|all}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ All checks completed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
