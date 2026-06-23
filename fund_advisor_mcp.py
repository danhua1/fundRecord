#!/usr/bin/env python3
"""
基金投顾系统 MCP 服务器 — 基于东方财富 & 天天基金 API
提供 MCP 工具调用和独立脚本执行两种模式
兼容 Cherry Studio 和其他 MCP 客户端
"""

import sys
import json
import asyncio
import logging
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 配置日志输出到stderr，避免干扰stdio通信
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# 导入原有的基金投顾模块
from fund_advisor import (
    v1_defensive, v2_balanced, v3_growth, v4_rotation, v5_index,
    fund_list, fund_ranking, fund_holdings, find_etf,
    score_funds, find_sector_top_funds, fund_type_map,
    main as original_main
)

# ============================================================
# MCP 服务器定义
# ============================================================

server = Server("fund-advisor")

logger.info("初始化 Fund Advisor MCP 服务器...")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出所有可用的MCP工具"""
    logger.info("客户端请求工具列表")
    return [
        Tool(
            name="get_portfolio_v1_defensive",
            description="获取V1稳健版基金组合推荐（债券为主，低风险⭐）",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_v2_balanced",
            description="获取V2均衡版基金组合推荐（股债平衡，中低风险⭐⭐）",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_v3_growth",
            description="获取V3成长版基金组合推荐（权益为主，中高风险⭐⭐⭐）",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_v4_rotation",
            description="获取V4行业轮动版基金组合推荐（实时行业动量驱动，高风险⭐⭐⭐⭐）",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_v5_index",
            description="获取V5指数版基金组合推荐（纯被动指数，中风险⭐⭐）",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_all_portfolios",
            description="获取所有五个版本的基金组合推荐（一次性获取全部策略）",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_fund",
            description="搜索基金信息（支持基金代码、名称关键词搜索）",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（基金名称或代码）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制（默认10）",
                        "default": 10
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_fund_holdings",
            description="获取指定基金的持仓信息和板块分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "基金代码（6位数字）"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份（默认2026）",
                        "default": 2026
                    },
                    "quarter": {
                        "type": "integer",
                        "description": "季度（1-4，默认1）",
                        "default": 1
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="get_fund_ranking",
            description="获取基金排名列表（支持按类型、排序方式筛选）",
            inputSchema={
                "type": "object",
                "properties": {
                    "fund_type": {
                        "type": "string",
                        "description": "基金类型：all(全部)/gp(股票)/hh(混合)/zq(债券)/qdii",
                        "default": "all",
                        "enum": ["all", "gp", "hh", "zq", "qdii"]
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "排序方式：zzf(近1年)/6y(近6月)/3y(近3年)/jn(今年以来)",
                        "default": "zzf",
                        "enum": ["zzf", "6y", "3y", "jn"]
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "返回数量（默认50，最大200）",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="find_sector_etf",
            description="查找指定板块的ETF基金",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "板块关键词（如：芯片、新能源、消费、医药等）"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_sector_top_funds",
            description="获取指定板块的头部主动管理基金",
            inputSchema={
                "type": "object",
                "properties": {
                    "sector": {
                        "type": "string",
                        "description": "板块名称（消费/科技/医药/新能源/金融/制造/周期等）",
                        "enum": ["消费", "科技", "医药", "新能源", "金融", "制造", "周期", "宽基"]
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "返回前N只基金（默认10）",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["sector"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[TextContent]:
    """处理工具调用"""

    logger.info(f"处理工具调用: {name}, 参数: {arguments}")

    try:
        if arguments is None:
            arguments = {}

        if name == "get_portfolio_v1_defensive":
            portfolio = v1_defensive()
            result = json.dumps(portfolio, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_portfolio_v2_balanced":
            portfolio = v2_balanced()
            result = json.dumps(portfolio, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_portfolio_v3_growth":
            portfolio = v3_growth()
            result = json.dumps(portfolio, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_portfolio_v4_rotation":
            portfolio = v4_rotation()
            result = json.dumps(portfolio, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_portfolio_v5_index":
            portfolio = v5_index()
            result = json.dumps(portfolio, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_all_portfolios":
            portfolios = [
                v1_defensive(),
                v2_balanced(),
                v3_growth(),
                v4_rotation(),
                v5_index(),
            ]
            result_data = {
                "portfolios": portfolios,
                "summary": {
                    "total": len(portfolios),
                    "risk_levels": [p["risk"] for p in portfolios]
                }
            }
            result = json.dumps(result_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "search_fund":
            keyword = arguments.get("keyword", "")
            limit = arguments.get("limit", 10)

            all_funds = fund_list()
            matches = [f for f in all_funds if keyword in f["name"] or keyword in f["code"]]
            matches = matches[:limit]

            result_data = {
                "keyword": keyword,
                "total_matches": len(matches),
                "funds": matches
            }
            result = json.dumps(result_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_fund_holdings":
            code = arguments.get("code", "")
            year = arguments.get("year", 2026)
            quarter = arguments.get("quarter", 1)

            holdings = fund_holdings(code, year, quarter)
            result_data = {
                "code": code,
                "period": f"{year}Q{quarter}",
                "holdings": holdings
            }
            result = json.dumps(result_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_fund_ranking":
            fund_type = arguments.get("fund_type", "all")
            sort_by = arguments.get("sort_by", "zzf")
            page_size = arguments.get("page_size", 50)

            ranking = fund_ranking(fund_type, sort_by, page_size)
            result_data = {
                "fund_type": fund_type,
                "sort_by": sort_by,
                "total": len(ranking),
                "funds": ranking
            }
            result = json.dumps(result_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "find_sector_etf":
            keyword = arguments.get("keyword", "")
            etf = find_etf(keyword)

            if etf:
                result_data = {
                    "keyword": keyword,
                    "found": True,
                    "etf": etf
                }
            else:
                result_data = {
                    "keyword": keyword,
                    "found": False,
                    "message": f"未找到关键词 '{keyword}' 对应的ETF"
                }
            result = json.dumps(result_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        elif name == "get_sector_top_funds":
            sector = arguments.get("sector", "")
            top_n = arguments.get("top_n", 10)

            # 获取混合型和股票型排名数据
            rank_data = fund_ranking("hh", "zzf", 200) + fund_ranking("gp", "zzf", 200)
            top_funds = find_sector_top_funds(sector, rank_data, top_n)

            result_data = {
                "sector": sector,
                "total": len(top_funds),
                "funds": top_funds
            }
            result = json.dumps(result_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

        else:
            error_data = {
                "error": f"未知工具: {name}",
                "available_tools": [
                    "get_portfolio_v1_defensive", "get_portfolio_v2_balanced",
                    "get_portfolio_v3_growth", "get_portfolio_v4_rotation",
                    "get_portfolio_v5_index", "get_all_portfolios",
                    "search_fund", "get_fund_holdings", "get_fund_ranking",
                    "find_sector_etf", "get_sector_top_funds"
                ]
            }
            result = json.dumps(error_data, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.error(f"工具调用失败: {e}", exc_info=True)
        error_data = {
            "error": str(e),
            "tool": name,
            "arguments": arguments
        }
        result = json.dumps(error_data, ensure_ascii=False, indent=2)
        return [TextContent(type="text", text=result)]


# ============================================================
# 主入口 — 支持MCP服务器和独立脚本两种模式
# ============================================================

async def run_mcp_server():
    """启动MCP服务器"""
    logger.info("启动 MCP 服务器（stdio 模式）...")

    async with stdio_server() as (read_stream, write_stream):
        logger.info("stdio 流已建立，开始运行服务器...")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fund-advisor",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


def main():
    """主入口函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        # MCP服务器模式
        logger.info("=== Fund Advisor MCP 服务器 ===")
        logger.info("模式: stdio")
        logger.info("工具数量: 11")
        asyncio.run(run_mcp_server())
    else:
        # 独立脚本模式 — 调用原始main函数
        original_main()


if __name__ == "__main__":
    main()
