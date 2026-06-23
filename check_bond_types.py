#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/dusiyuan/Documents/fundRecord')
from fund_advisor import fund_ranking, fund_type_map

ftype = fund_type_map()
bond_rank = fund_ranking("zq", sort_by="zzf", page_size=200)

# 统计各类型债券基金
type_count = {}
unknown_funds = []
for f in bond_rank:
    ft = ftype.get(f["code"], "未知")
    if ft not in type_count:
        type_count[ft] = []
    type_count[ft].append(f"{f['code']} {f['name']}")
    if ft == "未知":
        unknown_funds.append(f)

print(f"=== 债券基金分析（共{len(bond_rank)}只）===\n")

# 统计概览
print(f"类型覆盖率: {len(bond_rank) - len(unknown_funds)}/{len(bond_rank)} ({(len(bond_rank) - len(unknown_funds))/len(bond_rank)*100:.1f}%)")
print(f"缺失类型: {len(unknown_funds)} 只\n")

print("=" * 60)
print("各类型分布:")
for ft, funds in sorted(type_count.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{ft} ({len(funds)}个):")
    for fund in funds:
        print(f"  {fund}")

if unknown_funds:
    print("\n" + "=" * 60)
    print(f"\n⚠️  缺少类型数据的基金（{len(unknown_funds)}只）:")
    for f in unknown_funds[:20]:  # 只显示前20个
        print(f"  {f['code']} {f['name']}")
    if len(unknown_funds) > 20:
        print(f"  ... 还有 {len(unknown_funds) - 20} 只未显示")
