#!/usr/bin/env python3
"""
MCP 功能测试脚本
用于验证 fund_advisor_mcp.py 的工具是否正常工作
"""

import json
import asyncio
from fund_advisor_mcp import (
    v1_defensive, v2_balanced, v3_growth, v4_rotation, v5_index,
    fund_list, find_etf, fund_ranking
)


def test_portfolio_functions():
    """测试所有组合生成函数"""
    print("=" * 60)
    print("测试基金组合生成函数")
    print("=" * 60)

    tests = [
        ("V1 稳健版", v1_defensive),
        ("V2 均衡版", v2_balanced),
        ("V3 成长版", v3_growth),
        ("V4 行业轮动版", v4_rotation),
        ("V5 指数版", v5_index),
    ]

    results = []
    for name, func in tests:
        print(f"\n测试 {name}...")
        try:
            portfolio = func()
            print(f"✓ {name} 生成成功")
            print(f"  - 名称: {portfolio['name']}")
            print(f"  - 风险: {portfolio['risk']}")
            print(f"  - 配置数: {len(portfolio['allocations'])}")
            results.append((name, "成功", portfolio))
        except Exception as e:
            print(f"✗ {name} 失败: {e}")
            results.append((name, "失败", str(e)))

    return results


def test_search_functions():
    """测试搜索功能"""
    print("\n" + "=" * 60)
    print("测试搜索功能")
    print("=" * 60)

    # 测试基金列表
    print("\n1. 测试 fund_list()...")
    try:
        funds = fund_list()
        print(f"✓ 获取到 {len(funds)} 只基金")
        print(f"  示例: {funds[0]}")
    except Exception as e:
        print(f"✗ 失败: {e}")

    # 测试 ETF 查找
    print("\n2. 测试 find_etf()...")
    keywords = ["芯片", "新能源", "消费"]
    for kw in keywords:
        try:
            etf = find_etf(kw)
            if etf:
                print(f"✓ 找到 '{kw}' ETF: {etf['name']} ({etf['code']})")
            else:
                print(f"⚠ 未找到 '{kw}' 对应的 ETF")
        except Exception as e:
            print(f"✗ '{kw}' 查询失败: {e}")

    # 测试基金排名
    print("\n3. 测试 fund_ranking()...")
    try:
        ranking = fund_ranking("hh", "zzf", 10)
        print(f"✓ 获取到 {len(ranking)} 条排名数据")
        if ranking:
            print(f"  示例: {ranking[0]['name']} ({ranking[0]['code']})")
    except Exception as e:
        print(f"✗ 失败: {e}")


def test_json_serialization(portfolio_results):
    """测试 JSON 序列化（MCP 返回格式）"""
    print("\n" + "=" * 60)
    print("测试 JSON 序列化")
    print("=" * 60)

    for name, status, data in portfolio_results:
        if status == "成功":
            try:
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                print(f"✓ {name} JSON 序列化成功 ({len(json_str)} 字符)")
            except Exception as e:
                print(f"✗ {name} JSON 序列化失败: {e}")


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           基金投顾系统 MCP 功能测试                       ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # 测试组合生成
    portfolio_results = test_portfolio_functions()

    # 测试搜索功能
    test_search_functions()

    # 测试 JSON 序列化
    test_json_serialization(portfolio_results)

    # 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    success_count = sum(1 for _, status, _ in portfolio_results if status == "成功")
    total_count = len(portfolio_results)
    print(f"基金组合生成: {success_count}/{total_count} 成功")

    if success_count == total_count:
        print("\n✓ 所有测试通过，MCP 功能正常！")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit(main())
