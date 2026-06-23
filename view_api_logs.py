#!/usr/bin/env python3
"""
查看API调用日志的工具
"""

import json
import glob
import os
from datetime import datetime

def view_latest_log():
    """查看最新的API调用日志"""
    log_files = glob.glob("api_calls_*.json")

    if not log_files:
        print("未找到API调用日志文件")
        return

    # 按修改时间排序，取最新的
    latest = max(log_files, key=os.path.getmtime)

    print("=" * 80)
    print(f"📋 API调用日志分析: {latest}")
    print("=" * 80)

    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n总体统计:")
    print(f"  总调用次数: {data['total_calls']}")
    print(f"  成功: {data['successful_calls']} ({data['successful_calls']/data['total_calls']*100:.1f}%)")
    print(f"  失败: {data['failed_calls']} ({data['failed_calls']/data['total_calls']*100:.1f}%)")
    print(f"  总耗时: {data['total_duration']:.2f}秒")
    print(f"  平均耗时: {data['total_duration']/data['total_calls']:.3f}秒/次")

    # 按URL分组统计
    url_stats = {}
    for call in data['calls']:
        url = call['url'].split('?')[0]  # 去掉参数
        if url not in url_stats:
            url_stats[url] = {
                'count': 0,
                'success': 0,
                'failed': 0,
                'total_duration': 0,
                'total_retries': 0
            }

        url_stats[url]['count'] += 1
        if call.get('status') == 200:
            url_stats[url]['success'] += 1
        if call.get('error'):
            url_stats[url]['failed'] += 1
        url_stats[url]['total_duration'] += call.get('duration', 0)
        url_stats[url]['total_retries'] += call.get('retries', 0)

    print(f"\n按接口统计:")
    print(f"{'接口':<60} {'调用':<6} {'成功':<6} {'失败':<6} {'平均耗时':<10} {'重试'}")
    print("-" * 100)

    for url, stats in sorted(url_stats.items(), key=lambda x: -x[1]['count']):
        avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
        short_url = url if len(url) <= 58 else url[:55] + "..."
        print(f"{short_url:<60} {stats['count']:<6} {stats['success']:<6} {stats['failed']:<6} "
              f"{avg_duration:<10.3f} {stats['total_retries']}")

    # 显示失败的调用详情
    failed_calls = [c for c in data['calls'] if c.get('error')]
    if failed_calls:
        print(f"\n失败调用详情:")
        for i, call in enumerate(failed_calls, 1):
            print(f"\n{i}. {call['url']}")
            print(f"   时间: {call['timestamp']}")
            print(f"   参数: {call.get('params', 'N/A')}")
            print(f"   重试次数: {call.get('retries', 0)}")
            print(f"   耗时: {call.get('duration', 0):.3f}秒")
            print(f"   错误: {call['error']}")

    print()

def list_all_logs():
    """列出所有日志文件"""
    log_files = glob.glob("api_calls_*.json")

    if not log_files:
        print("未找到API调用日志文件")
        return

    print("=" * 80)
    print("所有API调用日志文件:")
    print("=" * 80)

    for log_file in sorted(log_files, key=os.path.getmtime, reverse=True):
        mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
        size = os.path.getsize(log_file)

        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\n{log_file}")
        print(f"  修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  文件大小: {size} 字节")
        print(f"  调用次数: {data['total_calls']}  成功: {data['successful_calls']}  失败: {data['failed_calls']}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        list_all_logs()
    else:
        view_latest_log()
