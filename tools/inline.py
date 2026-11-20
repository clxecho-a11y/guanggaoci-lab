#!/usr/bin/env python3
"""把 data.js 併進 index.html，產生只要上傳一個檔案的單檔版。
用法：python3 -I inline.py <index.html> <data.js> <輸出的 index.html>"""
import sys
page = open(sys.argv[1], encoding="utf-8").read()
data = open(sys.argv[2], encoding="utf-8").read()
tag = '<script src="data.js"></script>'
if page.count(tag) != 1:
    sys.exit("找不到 data.js 的載入標籤")
if "</script" in data.lower():
    sys.exit("data.js 裡有 </script，不能直接併入")
open(sys.argv[3], "w", encoding="utf-8").write(page.replace(tag, "<script>\n" + data + "</script>"))
print("ok", len(page), len(data))
