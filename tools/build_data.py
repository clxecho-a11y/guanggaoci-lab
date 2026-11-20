#!/usr/bin/env python3
"""植入口播文案實驗室 — 資料產生工具

用法：
  python3 -I build_data.py <廣告口播追蹤公開版的 data.json> <輸出的 data.js>

從口播追蹤頁的快照挑出實驗室需要的欄位，寫成 data.js（window.LAB_DATA = {...}）。
放上公開的 GitHub 之前刻意不帶的東西：銷售額與目標、觀眾數據、Drive 檔案連結與資料夾 ID、
頻道備註、每段口播的健康說法評語（health）。

銷量只以相對標記帶出（hi／mid／lo＝高於／接近／低於這個頻道平常），不帶任何金額或觀看數。算法見 sale_labels()。
"""
import collections
import datetime
import json
import re
import statistics
import sys

PRODUCTS = ["黑膏滋", "紅海參", "蔘皇", "藍莓優品"]
KIND_CAT = {"會員網": "會員網站", "短號推廣": "短號訂閱", "抽獎公布": "抽獎公布"}
SKIP_KINDS = {"未轉寫插播"}


def count_chars(text):
    """口播字數：中文字一個算一個，連續的英數算一個。"""
    return len(re.findall(r"[一-鿿]", text)) + len(re.findall(r"[A-Za-z0-9]+", text))


def cats_for(seg):
    kind = seg.get("kind") or ""
    if kind in KIND_CAT:
        return [KIND_CAT[kind]]
    adv = seg.get("adv") or ""
    found = [p for p in PRODUCTS if p in adv]
    return found or ["其他產品"]


def join_lines(rows, tags):
    return " ".join(r[1].strip() for r in rows if len(r) > 2 and r[2] in tags and r[1].strip())


def add_days(iso, n):
    return (datetime.date.fromisoformat(iso) + datetime.timedelta(days=n)).isoformat()


def is_batch(product, day):
    """紅海參每月 15 號和月底含訂閱制結算，不是口播帶來的，不計入。"""
    return product == "紅海參" and (day[8:] == "15" or add_days(day, 1)[8:] == "01")


SALE_MIN_DAYS = 4      # 一個頻道的一個產品至少要有幾個可比較的口播日才標記
SALE_HI, SALE_LO = 1.25, 0.75


def sale_labels(d):
    """每個「頻道 × 產品 × 口播日」的相對銷量標記。

    口播當天＋次日的同產品銷售額（和口播追蹤頁「銷量分析」同一個口徑：沒有銷售紀錄的日子算 0、
    退款負數算 0、紅海參結算日不計）÷ 這兩天頻道的觀看次數（長片＋直播，只用 YouTube 正式數字，
    暫定數字偏低不用），得到「每千次觀看的銷售額」；再除以這個頻道同產品所有口播日的中位數。
    每個頻道只和自己比。
    """
    sales = {(s["ch"], s["date"]): s for s in d["sales"]}
    max_s = max(s["date"] for s in d["sales"])
    views = {c["ch"]: (c.get("daily") or {}) for c in d.get("chaud", [])}

    def amt(ch, day, p):
        if is_batch(p, day):
            return None
        x = sales.get((ch, day))
        return max(0, (x.get("byClient") or {}).get(p, 0)) if x else 0

    ad_days = collections.defaultdict(set)
    for e in d["episodes"]:
        for s in e.get("segs") or []:
            if s.get("kind") != "產品廣告":
                continue
            for p in PRODUCTS:
                if p in (s.get("adv") or ""):
                    ad_days[(e["ch"], p)].add(e["date"])

    labels, stats = {}, {}
    for (ch, p), days in ad_days.items():
        rates = {}
        for day in days:
            d1 = add_days(day, 1)
            if d1 > max_s:
                continue
            a0, a1 = amt(ch, day, p), amt(ch, d1, p)
            v0, v1 = views.get(ch, {}).get(day), views.get(ch, {}).get(d1)
            if a0 is None or a1 is None or not v0 or not v1:
                continue
            rates[day] = (a0 + a1) / (v0 + v1) * 1000
        med = statistics.median(rates.values()) if rates else 0
        ok = len(rates) >= SALE_MIN_DAYS and med > 0
        stats[(ch, p)] = (len(days), len(rates), ok)
        if not ok:
            continue
        for day, r in rates.items():
            idx = r / med
            labels[(ch, p, day)] = "hi" if idx >= SALE_HI else "lo" if idx <= SALE_LO else "mid"
    return labels, stats


def main(src, dst):
    d = json.load(open(src, encoding="utf-8"))
    names = {c["slug"]: c["name"] for c in d["channels"]}
    order = {c["slug"]: c.get("order", 99) for c in d["channels"]}

    labels, sale_stats = sale_labels(d)
    segs = []
    rates = collections.defaultdict(list)
    codes = collections.defaultdict(collections.Counter)
    for e in d["episodes"]:
        ch = e.get("ch")
        if ch not in names:
            continue
        for i, s in enumerate(e.get("segs") or []):
            if s.get("kind") in SKIP_KINDS:
                continue
            rows = s.get("transcript") or []
            lead = join_lines(rows, ("lead",))
            core = join_lines(rows, ("core",))
            ret = join_lines(rows, ("ret",))
            if not core:
                continue
            n = count_chars(lead + core + ret)
            length = s.get("length") or 0
            if length and n > 30:
                rates[ch].append(n / length)
            code = (s.get("code") or "").strip()
            if code and "／" not in code and "/" not in code:
                codes[ch][code] += 1
            segs.append({
                "id": f"{e['__id'][:8]}-{i}",
                "ch": ch,
                "date": e["date"],
                "title": e.get("title") or "",
                "fmt": (e.get("fmt") or "").replace("（直播）", ""),
                "adv": s.get("adv") or "",
                "kind": s.get("kind") or "",
                "cats": cats_for(s),
                "slot": s.get("slot") or "",
                "pos": s.get("pos") or "",
                "pct": s.get("pct"),
                "start": s.get("start"),
                "len": length,
                "bucket": s.get("lenbucket") or "",
                "focus": s.get("focus") or [],
                "offer": s.get("offer") or [],
                "points": s.get("points") or [],
                "cta": s.get("cta") or [],
                "code": code,
                "member": s.get("member") or "",
                "note": s.get("note") or "",
                "n": n,
                "t": [lead, core, ret],
            })
            if s.get("kind") == "產品廣告":
                sale = {p: labels[(ch, p, e["date"])] for p in segs[-1]["cats"] if (ch, p, e["date"]) in labels}
                if sale:
                    segs[-1]["sale"] = sale

    segs.sort(key=lambda x: (x["date"], x["start"] or 0), reverse=True)
    all_rates = [r for v in rates.values() for r in v]
    channels = []
    for slug in sorted(names, key=lambda k: order[k]):
        v = rates.get(slug) or all_rates
        # 同一個優惠碼常有大小寫不同的寫法：先合併計數，再取最常見的那種寫法
        merged = collections.Counter()
        for k, v2 in codes[slug].items():
            merged[k.upper()] += v2
        top = merged.most_common(1)
        raw = [kv for kv in codes[slug].most_common() if top and kv[0].upper() == top[0][0]][:1]
        channels.append({
            "slug": slug,
            "name": names[slug],
            "rate": round(statistics.median(v), 2),
            "code": raw[0][0] if raw else "",
            "n": sum(1 for s in segs if s["ch"] == slug),
            # 每個產品有幾個口播日可以比較（只有天數，沒有金額）
            "saleN": {p: n for (c2, p), (_, n, ok) in sale_stats.items() if c2 == slug and ok},
        })

    out = {
        "built": d.get("built", ""),
        "from": min(s["date"] for s in segs),
        "to": max(s["date"] for s in segs),
        "channels": channels,
        "segs": segs,
    }
    body = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    # </script> 不會出現在 JSON 裡，但保險起見把 </ 跳脫掉
    body = body.replace("</", "<\\/")
    open(dst, "w", encoding="utf-8").write("window.LAB_DATA=" + body + ";\n")
    print("segs", len(segs), "channels", len(channels), "bytes", len(body.encode("utf-8")))
    for c in channels:
        print(" ", c["slug"], c["name"], "段數", c["n"], "語速", c["rate"], "優惠碼", c["code"])
    print("cats", collections.Counter(x for s in segs for x in s["cats"]))
    print("銷量標記", collections.Counter(v for s in segs for v in (s.get("sale") or {}).values()),
          "| 有標記的段數", sum(1 for s in segs if s.get("sale")), "／產品廣告", sum(1 for s in segs if s["kind"] == "產品廣告"))
    for (c2, p), (nd, nr, ok) in sorted(sale_stats.items()):
        print("  ", names[c2], p, "口播日", nd, "可比較", nr, "標記" if ok else "不標（樣本不足或中位數為 0）")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
