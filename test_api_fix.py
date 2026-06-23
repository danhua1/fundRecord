#!/usr/bin/env python3
"""
测试API调用日志记录和代理修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fund_advisor import em_get, _API_CALL_LOG, logger
import logging

# 设置日志级别为INFO以查看详细信息
logging.basicConfig(level=logging.INFO)

def test_api_call():
    """测试API调用和日志记录"""
    print("=" * 60)
    print("测试1: 基金列表API调用")
    print("=" * 60)

    try:
        url = "http://fund.eastmoney.com/js/fundcode_search.js"
        r = em_get(url, timeout=30)
        print(f"✓ 请求成功，状态码: {r.status_code}")
        print(f"✓ 返回数据长度: {len(r.text)} 字符")
    except Exception as e:
        print(f"✗ 请求失败: {e}")

    print("\n" + "=" * 60)
    print("测试2: 东方财富行业排名API调用")
    print("=" * 60)

    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "10", "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fs": "m:90+t:2",
            "fields": "f2,f3,f4,f12,f14,f104,f105,f140,f136",
        }
        r = em_get(url, params=params, timeout=15)
        print(f"✓ 请求成功，状态码: {r.status_code}")
        data = r.json()
        print(f"✓ 返回行业数量: {len(data.get('data', {}).get('diff', []))}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")

    # 显示调用日志
    print("\n" + "=" * 60)
    print("API调用日志统计")
    print("=" * 60)

    if _API_CALL_LOG:
        success = [c for c in _API_CALL_LOG if c.get("status") == 200]
        failed = [c for c in _API_CALL_LOG if c.get("error")]

        print(f"总调用次数: {len(_API_CALL_LOG)}")
        print(f"成功: {len(success)}")
        print(f"失败: {len(failed)}")
        print(f"\n详细日志:")

        for i, log in enumerate(_API_CALL_LOG, 1):
            status = "✓" if log.get("status") == 200 else "✗"
            print(f"\n{i}. {status} {log['url'][:60]}...")
            print(f"   时间: {log['timestamp']}")
            print(f"   状态: {log.get('status', 'N/A')}")
            print(f"   耗时: {log.get('duration', 0):.3f}s")
            print(f"   重试: {log.get('retries', 0)}次")
            if log.get('error'):
                print(f"   错误: {log['error']}")
    else:
        print("暂无调用日志")

if __name__ == "__main__":
    test_api_call()
