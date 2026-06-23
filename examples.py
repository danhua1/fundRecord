#!/usr/bin/env python3
"""
MCP 工具调用示例
演示如何在 Python 代码中使用 fund_advisor 的各项功能
"""

from fund_advisor import (
    v1_defensive, v2_balanced, v3_growth, v4_rotation, v5_index,
    fund_list, fund_ranking, fund_holdings, find_etf,
    find_sector_top_funds, fund_type_map
)
import json


def example_1_get_single_portfolio():
    """示例 1: 获取单个基金组合"""
    print("=" * 60)
    print("示例 1: 获取 V3 成长版基金组合")
    print("=" * 60)

    portfolio = v3_growth()

    print(f"\n组合名称: {portfolio['name']}")
    print(f"风险等级: {portfolio['risk']}")
    print(f"策略描述: {portfolio['desc']}")
    print(f"\n资产配置:")
    for alloc in portfolio['allocations']:
        print(f"  - {alloc['role']}: {alloc['weight']*100:.0f}%")

    # 查看第一个配置的基金列表
    if portfolio['allocations'][0]['funds']:
        print(f"\n{portfolio['allocations'][0]['role']} 示例基金:")
        for fund in portfolio['allocations'][0]['funds'][:3]:
            print(f"  {fund['code']} {fund['name']}")


def example_2_get_all_portfolios():
    """示例 2: 获取所有5个版本的组合"""
    print("\n" + "=" * 60)
    print("示例 2: 获取所有基金组合版本")
    print("=" * 60)

    portfolios = [
        v1_defensive(),
        v2_balanced(),
        v3_growth(),
        v4_rotation(),
        v5_index(),
    ]

    print(f"\n共生成 {len(portfolios)} 个组合版本:")
    for p in portfolios:
        print(f"  - {p['name']:<20} {p['risk']:<20} {p['desc'][:40]}...")


def example_3_search_funds():
    """示例 3: 搜索基金"""
    print("\n" + "=" * 60)
    print("示例 3: 搜索'消费'相关基金")
    print("=" * 60)

    all_funds = fund_list()
    keyword = "消费"
    matches = [f for f in all_funds if keyword in f['name']][:10]

    print(f"\n找到 {len(matches)} 只基金 (显示前10只):")
    for fund in matches:
        print(f"  {fund['code']} {fund['name']:<30} {fund['type']}")


def example_4_get_fund_holdings():
    """示例 4: 获取基金持仓"""
    print("\n" + "=" * 60)
    print("示例 4: 查询基金持仓（需要有效基金代码）")
    print("=" * 60)

    # 这里使用一个示例代码，实际使用时替换为有效代码
    code = "000001"  # 华夏成长

    print(f"\n查询基金 {code} 的持仓...")
    try:
        holdings = fund_holdings(code, year=2026, quarter=1)
        print(f"板块判断: {holdings['sector_hint']}")
        if holdings['stocks']:
            print(f"重仓股票 (前5只):")
            for stock in holdings['stocks'][:5]:
                print(f"  {stock['code']} {stock['name']:<12} {stock['ratio']:.2f}%")
    except Exception as e:
        print(f"查询失败: {e}")
        print("提示: 请确保基金代码有效且网络连接正常")


def example_5_find_etf():
    """示例 5: 查找板块 ETF"""
    print("\n" + "=" * 60)
    print("示例 5: 查找板块 ETF")
    print("=" * 60)

    keywords = ["芯片", "新能源", "消费", "医药"]

    print("\n查找以下板块的 ETF:")
    for kw in keywords:
        try:
            etf = find_etf(kw)
            if etf:
                print(f"  {kw:<10} -> {etf['code']} {etf['name']}")
            else:
                print(f"  {kw:<10} -> 未找到")
        except Exception as e:
            print(f"  {kw:<10} -> 查询失败: {e}")


def example_6_get_ranking():
    """示例 6: 获取基金排名"""
    print("\n" + "=" * 60)
    print("示例 6: 获取混合型基金排名（近1年收益）")
    print("=" * 60)

    ranking = fund_ranking(fund_type="hh", sort_by="zzf", page_size=10)

    print(f"\n混合型基金 TOP 10:")
    print(f"{'代码':<10} {'名称':<30} {'1年收益%':<12} {'规模(亿)':<12}")
    print("-" * 70)
    for fund in ranking:
        ret_1y = fund.get('ret_1y') or 0
        size = (fund.get('fund_size') or 0) / 10000
        print(f"{fund['code']:<10} {fund['name'][:28]:<30} {ret_1y:>+10.2f} {size:>10.2f}")


def example_7_get_sector_top_funds():
    """示例 7: 获取板块头部主动基金"""
    print("\n" + "=" * 60)
    print("示例 7: 获取'消费'板块头部主动管理基金")
    print("=" * 60)

    # 先获取排名数据
    rank_data = fund_ranking("hh", "zzf", 200)

    sector = "消费"
    top_funds = find_sector_top_funds(sector, rank_data, top_n=5)

    print(f"\n{sector}板块 TOP 5 主动基金:")
    if top_funds:
        print(f"{'代码':<10} {'名称':<30} {'类型':<10} {'1年收益%':<12}")
        print("-" * 70)
        for fund in top_funds:
            ret_1y = fund.get('ret_1y') or 0
            ftype = fund.get('type', '未知')
            print(f"{fund['code']:<10} {fund['name'][:28]:<30} {ftype:<10} {ret_1y:>+10.2f}")
    else:
        print(f"未找到 {sector} 板块的匹配基金")


def example_8_json_export():
    """示例 8: 导出 JSON 格式（MCP 返回格式）"""
    print("\n" + "=" * 60)
    print("示例 8: 导出 JSON 格式数据")
    print("=" * 60)

    portfolio = v1_defensive()

    # 转换为 JSON 字符串
    json_str = json.dumps(portfolio, ensure_ascii=False, indent=2)

    print(f"\nJSON 数据大小: {len(json_str)} 字符")
    print(f"前200个字符预览:")
    print(json_str[:200] + "...")

    # 可以保存到文件
    # with open('portfolio_v1.json', 'w', encoding='utf-8') as f:
    #     f.write(json_str)


def main():
    """运行所有示例"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         基金投顾系统 - Python API 使用示例               ║")
    print("╚══════════════════════════════════════════════════════════╝")

    try:
        example_1_get_single_portfolio()
        example_2_get_all_portfolios()
        example_3_search_funds()
        example_4_get_fund_holdings()
        example_5_find_etf()
        example_6_get_ranking()
        example_7_get_sector_top_funds()
        example_8_json_export()

        print("\n" + "=" * 60)
        print("✓ 所有示例执行完成")
        print("=" * 60)
        print("\n提示:")
        print("  - 这些函数可以在 MCP 服务器中通过工具调用")
        print("  - 也可以在 Python 代码中直接导入使用")
        print("  - 返回的数据结构都支持 JSON 序列化")

    except Exception as e:
        print(f"\n✗ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
