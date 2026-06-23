#!/bin/bash
# Cherry Studio MCP 验证脚本

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Cherry Studio MCP 集成验证脚本                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR="/Users/dusiyuan/Documents/fundRecord"
cd "$PROJECT_DIR"

# 1. 检查虚拟环境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 1: 检查虚拟环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".venv" ]; then
    echo "✓ 虚拟环境存在"
    source .venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q requests mcp
fi

# 2. 检查依赖
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 2: 检查依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if pip show mcp &>/dev/null && pip show requests &>/dev/null; then
    echo "✓ requests: $(pip show requests | grep Version | cut -d' ' -f2)"
    echo "✓ mcp: $(pip show mcp | grep Version | cut -d' ' -f2)"
else
    echo "✗ 依赖缺失，正在安装..."
    pip install -q requests mcp
fi

# 3. 测试 Python 脚本
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 3: 测试 MCP 服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from fund_advisor_mcp import server, handle_list_tools
import asyncio

async def test():
    tools = await handle_list_tools()
    print(f'✓ MCP 服务器配置正确')
    print(f'✓ 工具数量: {len(tools)}')
    return len(tools)

result = asyncio.run(test())
" 2>&1 | grep "✓"

if [ $? -eq 0 ]; then
    echo "✓ MCP 服务器测试通过"
else
    echo "✗ MCP 服务器测试失败"
    exit 1
fi

# 4. 显示配置信息
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 4: 配置信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Python 路径: $(which python3)"
echo "项目路径: $PROJECT_DIR"
echo "MCP 脚本: $PROJECT_DIR/fund_advisor_mcp.py"
echo ""

# 5. 生成 Cherry Studio 配置
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  步骤 5: Cherry Studio 配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "请将以下配置添加到 Cherry Studio 的配置文件中："
echo ""
echo "配置文件位置（macOS）:"
echo "  ~/Library/Application Support/cherry-studio/mcp_config.json"
echo ""
echo "配置内容："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << EOF
{
  "mcpServers": {
    "fund-advisor": {
      "command": "$(which python3)",
      "args": [
        "$PROJECT_DIR/fund_advisor_mcp.py",
        "--mcp"
      ],
      "env": {
        "PYTHONPATH": "$PROJECT_DIR",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
EOF
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 6. 下一步说明
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  下一步操作"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 复制上面的配置到 Cherry Studio 的配置文件"
echo "2. 完全重启 Cherry Studio"
echo "3. 在 Cherry Studio 中查看工具列表（应该有 11 个工具）"
echo "4. 在对话中测试：'请帮我获取 V3 成长版的基金组合推荐'"
echo ""
echo "✓ 验证完成！MCP 服务器已就绪。"
echo ""
