#!/usr/bin/env python3
"""
基金投顾系统 — 基于东方财富 & 天天基金 API
按「板块 → 基金」体系，输出 5 个版本的基金组合推荐。

依赖: requests
用法: source .venv/bin/activate && python3 fund_advisor.py
"""

import requests
import json
import re
import time
import math
import random
import atexit
import logging
from datetime import datetime
from collections import defaultdict
from typing import Optional

# ============================================================
# 基础配置
# ============================================================

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User-Agent 池，防止爬虫识别
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15",
]

# 自定义异常
class NetworkError(Exception):
    """网络请求异常"""
    pass

class ValidationError(Exception):
    """输入验证异常"""
    pass

# 评分配置常量
class ScoringConfig:
    SMALL_FUND_THRESHOLD = 5000  # 万元，小规模基金阈值（流动性风险）
    LARGE_FUND_THRESHOLD = 800000  # 万元，超大规模基金阈值（船大难调头）
    SMALL_FUND_PENALTY = 0.5
    LARGE_FUND_PENALTY = 0.3
    MAX_FEE_PENALTY = 0.5
    FEE_DIVISOR = 3.0
    TRADING_DAYS_6M = 125  # 半年约125个交易日
    TRADING_DAYS_1Y = 250  # 一年约250个交易日
    TRADING_DAYS_3Y = 750  # 三年约750个交易日

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": random.choice(USER_AGENTS)})
_LAST_CALL = 0
_CALL_INTERVAL = 0.6
_CACHE = {}

def cleanup_session():
    """程序退出时清理 Session"""
    SESSION.close()
    logger.info("Session 已清理")

atexit.register(cleanup_session)

# 板块关键词 → 名称匹配
SECTOR_KEYWORDS = {
    "消费": ["食品饮料", "消费", "白酒", "家电", "农业", "农牧"],
    "科技": ["芯片", "半导体", "人工智能", "AI", "5G", "计算机", "软件", "大数据", "云计算"],
    "新能源": ["新能源", "光伏", "锂电池", "新能源汽车", "碳中和", "电力"],
    "医药": ["医药", "医疗", "生物", "创新药", "中药", "医美"],
    "金融": ["银行", "证券", "券商", "保险", "金融"],
    "制造": ["军工", "高端装备", "机器人", "工业母机", "汽车", "制造"],
    "周期": ["煤炭", "钢铁", "有色", "化工", "石油", "基建"],
    "宽基": ["沪深300", "中证500", "创业板", "上证50", "科创50", "中证1000"],
    "债券": ["国债", "纯债", "信用债", "利率债", "可转债"],
    "海外": ["纳斯达克", "标普500", "恒生", "港股", "德国", "日经"],
}

TYPE_ABBR = {
    "混合型-偏股": "偏股混合", "混合型-灵活": "灵活混合",
    "混合型-偏债": "偏债混合", "混合型-平衡": "平衡混合",
    "指数型-股票": "股票指数", "股票型": "主动股票",
    "债券型-长债": "长债", "债券型-中短债": "中短债",
    "债券型-混合二级": "二级债", "债券型-混合一级": "一级债",
    "货币型-普通货币": "货币",
}

# 热门行业 ETF 关键词
HOT_SECTORS = ["新能源", "芯片", "半导体", "人工智能", "消费", "医药", "军工", "汽车", "银行", "证券", "煤炭", "有色", "农业"]

# V4 行业轮动：东财行业名 → ETF 搜索关键词
INDUSTRY_ETF_MAP = {
    "小金属": ["有色", "稀土", "矿业"],
    "非金属材料": ["材料", "非金属"],
    "半导体": ["半导体", "芯片"],
    "元件": ["电子", "芯片"],
    "医疗服务": ["医疗", "医药"],
    "保险": ["保险", "金融"],
    "证券": ["证券", "券商"],
    "非银金融": ["金融", "证券", "保险"],
    "银行": ["银行"],
    "白酒": ["白酒", "食品饮料", "消费"],
    "饮料制造": ["食品饮料", "消费"],
    "光伏设备": ["光伏", "新能源"],
    "电池": ["新能源", "锂电池"],
    "汽车": ["汽车", "新能源车"],
    "军工": ["军工", "国防"],
    "煤炭": ["煤炭", "能源"],
    "钢铁": ["钢铁"],
    "电力": ["电力", "公用事业"],
    "房地产": ["地产", "房地产"],
    "通信": ["通信", "5G"],
}


def _rate_limit():
    global _LAST_CALL
    now = time.time()
    wait = _CALL_INTERVAL - (now - _LAST_CALL)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL = time.time()


def em_get(url, params=None, headers=None, timeout=15, max_retries=3):
    _rate_limit()
    h = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://fund.eastmoney.com/"
    }
    if headers:
        h.update(headers)

    for attempt in range(max_retries):
        try:
            logger.debug(f"请求 {url}, 参数: {params}, 尝试: {attempt + 1}/{max_retries}")
            r = SESSION.get(url, params=params, headers=h, timeout=timeout)
            r.raise_for_status()  # 检查 HTTP 状态码
            r.encoding = "utf-8"
            return r
        except requests.Timeout as e:
            logger.warning(f"请求超时 {url}: {e}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 10)  # 指数退避，上限10秒
                logger.info(f"等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
            else:
                raise NetworkError(f"请求超时，已重试 {max_retries} 次: {url}") from e
        except requests.HTTPError as e:
            logger.error(f"HTTP 错误 {url}: {e}")
            if attempt < max_retries - 1 and e.response.status_code >= 500:
                wait_time = min(2 ** attempt, 10)
                time.sleep(wait_time)
            else:
                raise NetworkError(f"HTTP 错误 {e.response.status_code}: {url}") from e
        except requests.RequestException as e:
            logger.error(f"请求异常 {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 10))
            else:
                raise NetworkError(f"请求失败: {url}") from e


# ============================================================
# 1. 全量基金列表 (带缓存)
# ============================================================
def fund_list() -> list[dict]:
    if "fund_list" in _CACHE:
        return _CACHE["fund_list"]
    print("  ⏳ 拉取全量基金列表...", end=" ")
    r = em_get("http://fund.eastmoney.com/js/fundcode_search.js", timeout=30)
    text = r.text.replace("﻿", "")
    # 修复 ReDoS: 使用严格字符类替代 (.*?)，限制长度
    matches = re.findall(r'\["([^"]{1,20})","([^"]{1,50})","([^"]{1,100})","([^"]{1,30})","([^"]{1,10})"\]', text)
    funds = [{"code": m[0], "pinyin": m[1], "name": m[2], "type": m[3]} for m in matches]
    _CACHE["fund_list"] = funds
    print(f"{len(funds)} 只")
    return funds


def fund_type_map() -> dict:
    if "fund_type_map" in _CACHE:
        return _CACHE["fund_type_map"]
    m = {f["code"]: f["type"] for f in fund_list()}
    _CACHE["fund_type_map"] = m
    return m


# ============================================================
# 2. 基金排名 (修复版)
# ============================================================
def fund_ranking(
    fund_type: str = "all",
    sort_by: str = "zzf",
    page_size: int = 200,
    page: int = 1,
) -> list[dict]:
    """
    fund_type: all / gp(股票) / hh(混合) / zq(债券) / qdii
    sort_by: zzf(近1年) / 6y(近6月) / 3y(近3年) / jn(今年以来)
    返回: [{code, name, daily, weekly, monthly, ret_3m, ret_6m,
            ret_1y, ret_2y, ret_3y, ret_si, inception_date, fund_size, fee}]
    """
    cache_key = f"rank_{fund_type}_{sort_by}_{page}_{page_size}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    print(f"  ⏳ 拉取排名 (type={fund_type}, sort={sort_by})...", end=" ")
    url = "https://fund.eastmoney.com/data/rankhandler.aspx"
    params = {
        "op": "ph", "dt": "kf", "ft": fund_type,
        "rs": "", "gs": "0",
        "sc": sort_by, "st": "desc",
        "pi": str(page), "pn": str(page_size),
        "mg": "a", "v": "0.1",
    }
    r = em_get(url, params=params,
               headers={"Referer": "https://fund.eastmoney.com/data/fundranking.html"})
    text = r.text

    # 提取 datas:[...] 数组中的每个引号字符串
    m = re.search(r'datas:\[(.*?)\]', text, re.DOTALL)
    if not m:
        print("无数据")
        return []

    entries = re.findall(r'"([^"]*)"', m.group(1))
    if not entries:
        print("无条目")
        return []

    funds = []
    for entry in entries:
        parts = entry.split(",")
        if len(parts) < 15:
            continue
        try:
            def _f(v):
                """转 float，空值返回 None 以便后续 NAV 回退"""
                try:
                    return float(v) if v else None
                except ValueError:
                    return None

            funds.append({
                "code": parts[0],
                "name": parts[1],
                "date": parts[3] if len(parts) > 3 else "",
                "nav": _f(parts[4]) or 0,
                "daily": _f(parts[6]) if len(parts) > 6 else None,
                "weekly": _f(parts[7]) if len(parts) > 7 else None,
                "monthly": _f(parts[8]) if len(parts) > 8 else None,
                "ret_3m": _f(parts[9]) if len(parts) > 9 else None,
                "ret_6m": _f(parts[10]) if len(parts) > 10 else None,
                "ret_1y": _f(parts[11]) if len(parts) > 11 else None,
                "ret_2y": _f(parts[12]) if len(parts) > 12 else None,
                "ret_3y": _f(parts[13]) if len(parts) > 13 else None,
                "ret_si": _f(parts[14]) if len(parts) > 14 else None,
                "inception_date": parts[16] if len(parts) > 16 else "",
                "fund_size": _f(parts[18]) if len(parts) > 18 else None,
                "fee": parts[19] if len(parts) > 19 else "",
            })
        except (ValueError, IndexError):
            continue

    _CACHE[cache_key] = funds
    print(f"{len(funds)} 条")
    return funds


# ============================================================
# 3. 基金持仓 → 板块推断
# ============================================================
def fund_holdings(code: str, year: int = 2026, quarter: int = 1) -> dict:
    # 输入验证
    if not re.match(r'^\d{6}$', code):
        raise ValidationError(f"基金代码格式错误，应为6位数字: {code}")
    if not (2000 <= year <= 2050):
        raise ValidationError(f"year 必须在 2000-2050 之间，当前值: {year}")
    if quarter not in (1, 2, 3, 4):
        raise ValidationError(f"quarter 必须为 1-4，当前值: {quarter}")

    url = "https://fundf10.eastmoney.com/FundArchivesDatas.aspx"
    params = {
        "type": "jjcc", "code": code,
        "topline": "10", "year": str(year), "month": str(quarter * 3),
    }
    try:
        r = em_get(url, params=params, timeout=10)
        text = r.text
        # 修复 ReDoS: 限制字符类和长度
        rows = re.findall(
            r'<td[^>]{0,50}><a[^>]{0,100}>(\d{6})</a></td>\s*<td[^>]{0,50}><a[^>]{0,100}>([^<]{1,50})</a></td>.*?<td[^>]{0,50}>([\d.]{1,10})%</td>',
            text, re.DOTALL
        )
        stocks = []
        sector_weight = defaultdict(float)
        for row in rows:
            stock_name = row[1]
            ratio = float(row[2])
            stocks.append({"code": row[0], "name": stock_name, "ratio": ratio})
            for sector, keywords in SECTOR_KEYWORDS.items():
                if sector in ("债券", "海外", "宽基"):
                    continue
                for kw in keywords:
                    if kw in stock_name:
                        sector_weight[sector] += ratio
        hint = max(sector_weight, key=sector_weight.get) if sector_weight else "综合"
        return {"stocks": stocks, "sector_hint": hint}
    except (NetworkError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"获取持仓失败 {code}: {e}")
        return {"stocks": [], "sector_hint": "未知"}


# ============================================================
# 4. 多维度评分
# ============================================================
def score_funds(funds: list[dict], top_n: int = 30) -> list[dict]:
    if not funds:
        return []
    if len(funds) == 1:
        funds[0]["score"] = 0.5
        return funds

    def norm(vals, reverse=False):
        mn, mx = min(vals), max(vals)
        if mx == mn:
            return [0.5] * len(vals)
        if reverse:
            return [(mx - v) / (mx - mn) for v in vals]
        return [(v - mn) / (mx - mn) for v in vals]

    ret_1y = [f.get("ret_1y") or 0 for f in funds]
    ret_3y = [f.get("ret_3y") or 0 for f in funds]
    ret_6m = [f.get("ret_6m") or 0 for f in funds]
    sizes = [f.get("fund_size") or 0 for f in funds]

    n_1y = norm(ret_1y)
    n_3y = norm(ret_3y)
    n_6m = norm(ret_6m)
    n_size = norm(sizes)

    for i, f in enumerate(funds):
        sz = sizes[i]
        size_penalty = 0
        if 0 < sz < ScoringConfig.SMALL_FUND_THRESHOLD:
            size_penalty = ScoringConfig.SMALL_FUND_PENALTY
        elif sz > ScoringConfig.LARGE_FUND_THRESHOLD:
            size_penalty = ScoringConfig.LARGE_FUND_PENALTY

        fee_str = f.get("fee", "0%") or "0%"
        try:
            fee_val = float(fee_str.replace("%", ""))
        except ValueError:
            fee_val = 0
        fee_penalty = min(fee_val / ScoringConfig.FEE_DIVISOR, ScoringConfig.MAX_FEE_PENALTY)

        f["score"] = round(
            0.30 * n_1y[i] + 0.20 * n_3y[i] + 0.15 * n_6m[i]
            + 0.10 * (1 - n_size[i])
            - 0.15 * fee_penalty - 0.10 * size_penalty,
            4
        )

    funds.sort(key=lambda x: x.get("score", 0), reverse=True)
    return funds[:top_n]


# ============================================================
# 5. 查找最佳 ETF (通用) + 性能优化索引
# ============================================================
def build_fund_index() -> dict[str, list[dict]]:
    """构建基金名称倒排索引，加速查询"""
    if "fund_index" in _CACHE:
        return _CACHE["fund_index"]

    index = defaultdict(list)
    all_funds = fund_list()

    # 构建关键词索引
    index_keywords = ["ETF", "联接", "指数"] + list(SECTOR_KEYWORDS.keys())
    for kw in HOT_SECTORS:
        if kw not in index_keywords:
            index_keywords.append(kw)

    for fund in all_funds:
        for keyword in index_keywords:
            if keyword in fund["name"]:
                index[keyword].append(fund)

    _CACHE["fund_index"] = index
    logger.info(f"基金索引构建完成，索引关键词: {len(index_keywords)} 个")
    return index


def find_etf(keyword: str, exclude_faqi: bool = True) -> Optional[dict]:
    """从全量基金列表中按关键词匹配最佳 ETF/指数基金（使用索引优化）"""
    # 输入验证
    if not keyword or len(keyword) > 50:
        raise ValidationError(f"关键词长度必须在 1-50 之间: {keyword}")
    if not re.match(r'^[一-龥a-zA-Z0-9]+$', keyword):
        raise ValidationError(f"关键词只能包含中文、字母、数字: {keyword}")

    # 尝试使用索引
    index = build_fund_index()
    if keyword in index:
        candidates = index[keyword]
    else:
        # 回退到全量搜索
        all_f = fund_list()
        candidates = [f for f in all_f if keyword in f["name"]]

    matches = [f for f in candidates
               if any(tag in f["name"] for tag in ["ETF", "联接", "指数"])]

    if exclude_faqi:
        matches = [m for m in matches if "发起式" not in m["name"]]
    # 优先 A 类
    for m in matches:
        if m["name"].endswith("A") or "A" in m["name"].split("联接")[-1][:2]:
            return m
    return matches[0] if matches else None


def fund_ranking_batch(fund_type: str, sort_by: str, pages: int = 3, page_size: int = 200) -> list[dict]:
    """批量拉取多页排名数据，减少重复调用"""
    results = []
    for page in range(1, pages + 1):
        page_data = fund_ranking(fund_type, sort_by, page_size, page)
        results.extend(page_data)
    return results


# ============================================================
# 6. 关联排名数据到基金列表
# ============================================================
def enrich_with_ranking(funds: list[dict], rank_data: list[dict], nav_fallback: bool = True) -> list[dict]:
    """将排名数据（业绩/规模/费率）合并到基金列表条目，可选 NAV 回退"""
    rank_map = {f["code"]: f for f in rank_data}
    missing = []
    for fund in funds:
        if fund["code"] in rank_map:
            r = rank_map[fund["code"]]
            for key in ["ret_1y", "ret_3y", "ret_6m", "ret_3m", "ret_2y",
                         "daily", "weekly", "monthly", "fund_size", "fee"]:
                rv = r.get(key)
                if rv is not None and fund.get(key) is None:
                    fund[key] = rv
        if fund.get("ret_1y") is None:
            missing.append(fund)

    if nav_fallback and missing:
        enrich_with_nav_fallback(missing)
    return funds


# ============================================================
# 6b. NAV 历史回退 — 对缺失收益率数据的基金补充计算
# ============================================================
def enrich_with_nav_fallback(funds: list[dict]) -> list[dict]:
    """对 ret_1y 仍为空的基金，通过净值历史计算近1年收益"""
    need_fallback = [f for f in funds if not f.get("ret_1y")]
    if not need_fallback:
        return funds

    print(f"    ⏳ NAV 回退计算 {len(need_fallback)} 只基金...", end=" ")
    for fund in need_fallback:
        code = fund["code"]
        nav_data = fund_nav_fast(code)
        if nav_data:
            fund["ret_1y"] = nav_data.get("ret_1y", 0)
            fund["ret_3y"] = nav_data.get("ret_3y", 0)
            fund["ret_6m"] = nav_data.get("ret_6m", 0)
            fund["fund_size"] = nav_data.get("fund_size", fund.get("fund_size", 0))
            fund["fee"] = nav_data.get("fee", fund.get("fee", ""))
    print("done")
    return funds


def fund_nav_fast(code: str) -> Optional[dict]:
    """快速获取基金近期净值用于计算收益（取最新 + 半年前 + 1年前 + 3年前 点位）"""
    try:
        url = "https://api.fund.eastmoney.com/f10/lsjz"
        # 先拿最新净值
        params = {"fundCode": code, "pageIndex": "1", "pageSize": "3", "callback": "jQuery"}
        r = em_get(url, params=params,
                    headers={"Referer": "https://fundf10.eastmoney.com/"}, timeout=10)
        text = r.text
        start = text.index("(") + 1
        end = text.rindex(")")
        data = json.loads(text[start:end])
        nav_list = data.get("Data", {}).get("LSJZList", [])
        if not nav_list:
            return None
        latest_nav = float(nav_list[0]["DWJZ"])
        latest_date = nav_list[0]["FSRQ"]

        # 获取半年前的净值（大概125个交易日 ≈ 180天）
        ret_6m = 0
        params["pageIndex"] = "1"
        params["pageSize"] = "180"
        r2 = em_get(url, params=params,
                     headers={"Referer": "https://fundf10.eastmoney.com/"}, timeout=10)
        data2 = json.loads(r2.text[r2.text.index("(") + 1:r2.text.rindex(")")])
        nav_list_6m = data2.get("Data", {}).get("LSJZList", [])
        if len(nav_list_6m) > ScoringConfig.TRADING_DAYS_6M:
            old_6m = float(nav_list_6m[-1]["DWJZ"])
            ret_6m = round((latest_nav - old_6m) / old_6m * 100, 1)

        # 获取1年前的净值（~250个交易日）
        ret_1y = 0
        for page in range(1, 4):
            params["pageIndex"] = str(page)
            params["pageSize"] = "100"
            r3 = em_get(url, params=params,
                         headers={"Referer": "https://fundf10.eastmoney.com/"}, timeout=10)
            data3 = json.loads(r3.text[r3.text.index("(") + 1:r3.text.rindex(")")])
            nav_list_1y = data3.get("Data", {}).get("LSJZList", [])
            if len(nav_list_1y) >= ScoringConfig.TRADING_DAYS_1Y - (page - 1) * 100 or page == 3:
                # Use earliest NAV in the batch
                old_1y = float(nav_list_1y[-1]["DWJZ"])
                ret_1y = round((latest_nav - old_1y) / old_1y * 100, 1)
                break

        return {"ret_1y": ret_1y, "ret_3y": 0, "ret_6m": ret_6m, "fund_size": 0, "fee": ""}
    except (NetworkError, json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
        logger.warning(f"NAV 回退失败 {code}: {e}")
        return None


# ============================================================
# 7. 五个版本生成
# ============================================================

def v1_defensive() -> dict:
    """V1 稳健版：债券为主"""
    print("\n🛡️  V1 稳健版...")
    ftype = fund_type_map()

    # 债券排名 — 使用批量请求替代多次调用
    bond_rank = fund_ranking_batch("zq", sort_by="zzf", pages=3, page_size=200)

    long_bond = [f for f in bond_rank if "长债" in ftype.get(f["code"], "")]
    short_bond = [f for f in bond_rank if "中短债" in ftype.get(f["code"], "")]
    for f in long_bond + short_bond:
        f["type"] = ftype.get(f["code"], "债券型")
    long_bond = score_funds(long_bond, top_n=4)
    short_bond = score_funds(short_bond, top_n=3)

    # 偏债混合 — 也拉更多
    hh_rank = fund_ranking("hh", sort_by="zzf", page_size=200)
    if len([f for f in hh_rank if "偏债" in ftype.get(f["code"], "")]) < 2:
        hh_rank += fund_ranking("hh", sort_by="zzf", page_size=200, page=2)
    mixed_bond = [f for f in hh_rank if "偏债" in ftype.get(f["code"], "")]
    for f in mixed_bond:
        f["type"] = ftype.get(f["code"], "混合型")
    mixed_bond = score_funds(mixed_bond, top_n=2)

    # 货币基金
    money_funds = [f for f in fund_list() if f["type"] == "货币型-普通货币"][:3]
    money_funds = score_funds(money_funds, top_n=2)

    return {
        "name": "V1 稳健版",
        "desc": "债券固收为主(70%) + 偏债混合(20%) + 货币(10%)，适合保守型",
        "risk": "低风险 ⭐",
        "allocations": [
            {"role": "长债底仓", "funds": long_bond[:3], "weight": 0.35},
            {"role": "中短债增强", "funds": short_bond[:2], "weight": 0.25},
            {"role": "偏债混合", "funds": mixed_bond, "weight": 0.20},
            {"role": "货币现金", "funds": money_funds, "weight": 0.20},
        ],
    }


def v2_balanced() -> dict:
    """V2 均衡版：股债平衡"""
    print("\n⚖️  V2 均衡版...")
    ftype = fund_type_map()

    # 宽基指数 ETF — 用 ft=zs (指数型) 排名
    idx_rank = fund_ranking("zs", sort_by="zzf", page_size=300)
    broad_kw = ["沪深300", "中证500", "创业板"]
    broad_funds = []
    for kw in broad_kw:
        etf = find_etf(kw)
        if etf:
            broad_funds.append(etf)
    broad_funds = enrich_with_ranking(broad_funds, idx_rank)
    broad_funds = score_funds(broad_funds, top_n=3)

    # 偏股混合
    hh_rank = fund_ranking("hh", sort_by="zzf", page_size=200)
    equity = [f for f in hh_rank if ftype.get(f["code"], "") in ("混合型-偏股", "混合型-灵活")]
    for f in equity:
        f["type"] = ftype.get(f["code"], "混合型")
    equity = score_funds(equity, top_n=3)

    # 纯债 — 使用批量请求
    bond_rank = fund_ranking_batch("zq", sort_by="zzf", pages=2, page_size=200)
    bonds = [f for f in bond_rank if "长债" in ftype.get(f["code"], "")]
    for f in bonds:
        f["type"] = ftype.get(f["code"], "债券型")
    bonds = score_funds(bonds, top_n=3)

    return {
        "name": "V2 均衡版",
        "desc": "宽基(30%) + 偏股混合(20%) + 纯债(40%) + 现金(10%)，稳健增长",
        "risk": "中低风险 ⭐⭐",
        "allocations": [
            {"role": "宽基指数", "funds": broad_funds, "weight": 0.30},
            {"role": "偏股混合", "funds": equity, "weight": 0.20},
            {"role": "纯债底仓", "funds": bonds[:2], "weight": 0.30},
            {"role": "中短债", "funds": bonds[2:3], "weight": 0.10},
            {"role": "货币现金", "funds": [], "weight": 0.10},
        ],
    }


def v3_growth() -> dict:
    """V3 成长版：权益为主"""
    print("\n🚀  V3 成长版...")
    ftype = fund_type_map()

    # 行业 ETF — 用 ft=zs (指数型) 排名
    all_f = fund_list()
    idx_rank = fund_ranking("zs", sort_by="6y", page_size=400)

    sector_picks = []
    seen_codes = set()
    for kw in HOT_SECTORS:
        matches = [f for f in all_f if kw in f["name"]
                   and any(t in f["name"] for t in ["ETF", "联接", "指数"])
                   and "发起式" not in f["name"]
                   and f["code"] not in seen_codes]
        if matches:
            best = matches[0]
            if best["name"].endswith("A") or "A" not in best["name"]:
                pass
            else:
                # Prefer A share
                a_ver = [m for m in matches if "A" in m["name"]]
                best = a_ver[0] if a_ver else best
            seen_codes.add(best["code"])
            sector_picks.append(best)

    sector_picks = enrich_with_ranking(sector_picks, idx_rank)
    sector_picks = score_funds(sector_picks, top_n=6)

    # 主动权益
    hh_rank = fund_ranking("hh", sort_by="6y", page_size=200)
    active = [f for f in hh_rank if ftype.get(f["code"], "") in ("混合型-偏股", "股票型")]
    for f in active:
        f["type"] = ftype.get(f["code"], "混合型")
    active = score_funds(active, top_n=3)

    return {
        "name": "V3 成长版",
        "desc": "行业ETF(50%) + 主动权益(30%) + 现金(20%)，捕捉强势赛道",
        "risk": "中高风险 ⭐⭐⭐",
        "allocations": [
            {"role": "行业ETF组合", "funds": sector_picks, "weight": 0.50},
            {"role": "主动权益精选", "funds": active, "weight": 0.30},
            {"role": "货币/短债", "funds": [], "weight": 0.20},
        ],
    }


def v4_rotation() -> dict:
    """V4 行业轮动版：实时行业排名驱动"""
    print("\n🔄  V4 行业轮动版...")

    # 获取实时行业排名
    industries = []
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "100", "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fs": "m:90+t:2",
            "fields": "f2,f3,f4,f12,f14,f104,f105,f140,f136",
        }
        r = em_get(url, params=params, timeout=15)
        data = r.json()
        for i, item in enumerate(data.get("data", {}).get("diff", [])):
            industries.append({
                "rank": i + 1,
                "name": item.get("f14", ""),
                "change_pct": item.get("f3", 0),
                "code": item.get("f12", ""),
                "up_count": item.get("f104", 0),
                "down_count": item.get("f105", 0),
                "leader": item.get("f140", ""),
            })
        print(f"    实时行业排名: {len(industries)} 个行业")
    except Exception as e:
        print(f"    ⚠️ 行业排名失败: {e}")

    # 取当日涨幅 TOP 行业
    top_ind = sorted(industries, key=lambda x: -x["change_pct"])[:10]

    # 匹配 ETF
    all_f = fund_list()
    idx_rank = fund_ranking("zs", sort_by="6y", page_size=400)

    rotation_funds = []
    seen = set()
    for ind in top_ind:
        name = ind["name"]
        # 使用映射表 + 行业名本身的变体
        search_kws = INDUSTRY_ETF_MAP.get(name, [name, name.replace("Ⅱ", "").replace("Ⅲ", "")])
        for kw in search_kws:
            if len(kw) < 2:
                continue
            matches = [f for f in all_f if kw in f["name"]
                       and any(t in f["name"] for t in ["ETF", "联接", "指数"])
                       and f["code"] not in seen]
            for m in matches[:2]:
                seen.add(m["code"])
                m["sector"] = name
                m["sector_change"] = ind["change_pct"]
                rotation_funds.append(m)
            if matches:
                break

    rotation_funds = enrich_with_ranking(rotation_funds, idx_rank)
    rotation_funds = score_funds(rotation_funds, top_n=6)

    hot_names = ", ".join([i["name"] for i in top_ind[:5]])
    return {
        "name": "V4 行业轮动版",
        "desc": f"实时行业动量驱动，当前强势: {hot_names}",
        "risk": "高风险 ⭐⭐⭐⭐",
        "hot_industries": top_ind[:8],
        "allocations": [
            {"role": "行业轮动ETF", "funds": rotation_funds, "weight": 0.80},
            {"role": "货币/短债", "funds": [], "weight": 0.20},
        ],
    }


def v5_index() -> dict:
    """V5 指数版：纯被动"""
    print("\n📈  V5 指数版...")

    broad = [
        ("沪深300", 0.20), ("中证500", 0.15), ("创业板", 0.10),
        ("科创50", 0.10), ("上证50", 0.10),
    ]
    satellites = [
        ("消费", 0.06), ("医药", 0.05), ("新能源", 0.05),
        ("芯片", 0.05), ("银行", 0.05), ("军工", 0.04),
        ("港股", 0.05),
    ]

    idx_rank = fund_ranking("zs", sort_by="zzf", page_size=400)
    all_picks = []

    for kw, w in broad + satellites:
        etf = find_etf(kw)
        if etf:
            etf["target_weight"] = w
            all_picks.append(etf)

    all_picks = enrich_with_ranking(all_picks, idx_rank)

    broad_picks = all_picks[:len(broad)]
    sat_picks = all_picks[len(broad):]

    return {
        "name": "V5 指数版",
        "desc": "核心宽基(65%) + 行业卫星(35%)，纯被动低费率，适合长期定投",
        "risk": "中风险 ⭐⭐",
        "allocations": [
            {"role": "核心宽基", "funds": broad_picks, "weight": 0.65},
            {"role": "行业卫星", "funds": sat_picks, "weight": 0.35},
        ],
    }


# ============================================================
# 8. 输出
# ============================================================
def print_portfolio(p: dict):
    print(f"\n{'='*85}")
    print(f"  {p['name']}  |  {p['risk']}")
    print(f"  {p['desc']}")
    print(f"{'='*85}")

    if "hot_industries" in p:
        print(f"\n  🔥 当日强势行业:")
        for s in p["hot_industries"][:5]:
            print(f"     {s['rank']:>3}. {s['name']:<12}  {s['change_pct']:>+5.1f}%  "
                  f"涨{s['up_count']}跌{s['down_count']}  领涨:{s['leader']}")

    for alloc in p["allocations"]:
        role = alloc["role"]
        weight = alloc["weight"]
        funds = alloc["funds"]
        print(f"\n  ▸ {role} ({weight*100:.0f}%)")
        if not funds:
            print(f"     (自行选择货币基金/短债基金)")
            continue
        hdr = f"     {'代码':<8} {'名称':<30} {'类型':<8} {'1年%':>7} {'3年%':>7} {'规模(亿)':>9} {'费率':>6}"
        print(hdr)
        print(f"     {'-'*78}")
        for f in funds:
            code = f.get("code", "")
            name = f.get("name", "")[:28]
            ft_raw = f.get("type", "")
            ft = TYPE_ABBR.get(ft_raw, ft_raw)[:8]
            r1 = f.get("ret_1y") or 0
            r3 = f.get("ret_3y") or 0
            sz = (f.get("fund_size") or 0) / 10000  # 万元→亿
            fee = f.get("fee", "-") or "-"
            sc = f.get("score", 0) or 0
            print(f"     {code:<8} {name:<30} {ft:<8} {r1:>+6.1f} {r3:>+6.1f} {sz:>8.1f} {fee:>6}")

    print()


# ============================================================
# 9. Main
# ============================================================
def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       📊 基金投顾系统 — 板块×基金 五维组合推荐          ║")
    print("║       数据来源: 东方财富 · 天天基金 (实时)               ║")
    print(f"║       生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}                               ║")
    print("╚══════════════════════════════════════════════════════════╝")

    portfolios = [
        v1_defensive(),
        v2_balanced(),
        v3_growth(),
        v4_rotation(),
        v5_index(),
    ]

    for p in portfolios:
        print_portfolio(p)

    # 汇总
    print(f"{'='*85}")
    print(f"  📋 五版本速览")
    print(f"{'='*85}")
    print(f"  {'版本':<16} {'风险':<14} {'策略概要':<50}")
    print(f"  {'-'*80}")
    for p in portfolios:
        print(f"  {p['name']:<16} {p['risk']:<14} {p['desc'][:48]}")
    print()
    print("  ⚠️  免责声明：以上数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
    print()


if __name__ == "__main__":
    main()
