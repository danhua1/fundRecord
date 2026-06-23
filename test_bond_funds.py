#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/dusiyuan/Documents/fundRecord')
from fund_advisor import fund_ranking, fund_type_map

# 测试债券基金筛选
ftype = fund_type_map()
bond_rank = fund_ranking("zq", sort_by="zzf", page_size=200)

print(f"债券排名数据总数: {len(bond_rank)}")

long_bond = [f for f in bond_rank if "长债" in ftype.get(f["code"], "")]
short_bond = [f for f in bond_rank if "中短债" in ftype.get(f["code"], "")]

print(f"\n长债基金数量: {len(long_bond)}")
print(f"中短债基金数量: {len(short_bond)}")

print("\n前5个债券基金类型:")
for i, f in enumerate(bond_rank[:5]):
    print(f"{i+1}. {f['code']} {f['name'][:20]} - 类型: {ftype.get(f['code'], '未知')}")

print("\n中短债筛选示例:")
for i, f in enumerate(bond_rank[:20]):
    ft = ftype.get(f['code'], '')
    if "中短债" in ft or "短债" in ft:
        print(f"  {f['code']} {f['name'][:25]} - {ft}")
