#!/bin/bash
# 基金投顾系统 - 快速测试脚本

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       基金投顾系统 MCP 功能快速测试                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "✓ 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "✓ 检查依赖..."
pip install -q requests 2>/dev/null
pip install -q mcp 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试 1: 原始脚本模式（传统模式）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "运行命令: python3 fund_advisor.py"
echo ""
read -p "按 Enter 继续测试原始脚本..."
python3 fund_advisor.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试 2: MCP 功能测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "运行命令: python3 test_mcp.py"
echo ""
read -p "按 Enter 继续测试 MCP 功能..."
python3 test_mcp.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试 3: Python API 示例"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "运行命令: python3 examples.py"
echo ""
read -p "按 Enter 继续运行示例..."
python3 examples.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✓ 所有测试已完成"
echo ""
echo "下一步操作:"
echo "  1. 查看 MCP 使用说明: cat MCP_USAGE.md"
echo "  2. 配置 Claude Code: 使用 mcp_config.json"
echo "  3. 启动 MCP 服务器: python3 fund_advisor_mcp.py --mcp"
echo ""
