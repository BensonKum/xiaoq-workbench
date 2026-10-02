# -*- coding: utf-8 -*-
# 生成小Q工作台 8 個流程可視圖頁 (workflows/*.html)
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "workflows")
os.makedirs(OUT, exist_ok=True)

# 每個流程：slug, 標題, 觸發口令, steps[(名,描述)]
FLOWS = [
  {
    "slug":"cdm", "title":"錢大媽 CDM 自動化",
    "code":"CDM",
    "steps":[
      ("📥 下載 Yahoo 訂單", "step1 由 sap@qdama.cn 下載附件（防重複：marker + PDF 雙重檢查）"),
      ("📋 更新執貨入箱表", "step2 寫入 執貨入箱表_{target}.xlsx"),
      ("🧾 更新錢大媽發票", "step3 寫入 錢大媽發票_{ddmmyyyy}.xls"),
      ("🖨️ 打印 / 匯出 PDF", "step4 打印機輸出 + 匯出 PDF（TOSHIBA IP 192.168.1.199）"),
      ("📲 微信發送", "step5 發 PDF 去微信（cron 約 19:50 觸發）"),
      ("📧 郵件發送", "step6 發 PDF 去 bensonkum86@gmail.com"),
    ],
    "note":"⏰ 每晚 19:40 / 20:30 / 21:30 三輪自動跑（公司機鎖屏即可）。target_date = 今日 + 2 天。防重複：第一輪標記後，後兩輪自動跳過。"
  },
  {
    "slug":"new-product", "title":"新增產品",
    "code":"新產品 / 上新產品",
    "steps":[
      ("📖 讀工作指引", "先讀 產品更新工作指引.md（改名/新增/停售必讀）"),
      ("❓ 問三項", "產品名 / 價錢 / 分類（SKU 按 YH 規則自動編）"),
      ("🗂️ 改 products_v2.json", "canonical 產品資料（名/SKU/分類/local_img）"),
      ("🏪 改 inventory.html", "倉存系統動態讀 products_v2.json（唔使手改卡）"),
      ("🔥 Firestore inventory doc", "開 inventory doc（id=產品名，含 central 庫存）"),
      ("🖼️ 借圖 / 上圖", "冇實物相先借佔位圖，之後補 local_img"),
      ("🔄 sync + deploy + push", "sync products → firebase deploy → commit+push GitHub"),
    ],
    "note":"⚠️ 雙軌維護：products_v2.json（標準源）+ index.html（前台）+ Firestore 三方要同步。改完必 deploy 否則前台睇唔到。"
  },
  {
    "slug":"del-product", "title":"刪除 / 下架產品",
    "code":"刪除產品 / 下架產品",
    "steps":[
      ("❓ 問方式", "隱藏（推薦）定完全刪除？"),
      ("🙈 隱藏方案", "products_v2.json 設 hidden:true → 倉存隱藏，前台仍可售"),
      ("🗑️ 完全刪除", "移除 JSON 項 + Firestore doc（保留歷史用 hidden 較安全）"),
      ("🔄 deploy + push", "firebase deploy → commit+push"),
    ],
    "note":"💡 建議用 hidden:true 而非真刪，留低歷史訂單記錄（例如鮑魚罐頭）。"
  },
  {
    "slug":"ab-card", "title":"AB 卡（雙規格）",
    "code":"AB卡 / 雙規格卡",
    "steps":[
      ("🪧 一卡雙 SKU", "base SKU + 尾 A（例如 YH201 / YH201A）"),
      ("🏷️ 名稱含 +", "SKU 名稱要含「+」字符解析 Tab 標籤（如 椰菜鮮肉餃+麵）"),
      ("🔀 Tab 切換", "前台/inventory 用 Tab 切 base / A 規格"),
      ("📑 標準文檔", "詳見 docs/AB卡做法.md"),
    ],
    "note":"📌 SKU 尾 A 自動配對；用 getPackOptions() 識別單/多包裝。"
  },
  {
    "slug":"sync-products", "title":"Firestore /products 同步",
    "code":"sync products",
    "steps":[
      ("🐍 跑腳本", "python sync_products_to_firestore.py（Admin SDK）"),
      ("📤 寫入雲", "推 products_v2.json 全款上 /products 集合"),
      ("✅ 驗證", "server /products doc 數 = JSON 款數 + 5 孤兒（菠菜/紫薯/南瓜/蕃茄/豆乳麵）"),
    ],
    "note":"⚠️ Firestore security rule 未部署 /products match（暫 allow read:if true），清理待辦中。"
  },
  {
    "slug":"quote", "title":"祐興報價單 Excel",
    "code":"報價單",
    "steps":[
      ("🐍 跑腳本", "python gen_quote_xlsx.py（來源 products_v2.json）"),
      ("🖼️ 配圖", "匹配 images/ 相（缺相款用預留位）"),
      ("🗂️ 分類分組", "11 分類分組 + 分類 header（橙）"),
      ("📧 發出", "send 去微信 / 或加 E 欄網站連結"),
    ],
    "note":"📊 現 103 款（剔走雜項+贈品 4 款）。頂部預留公司名+Logo 位。"
  },
  {
    "slug":"beatra", "title":"Beatra 15 秒廣告片",
    "code":"廣告片",
    "steps":[
      ("💰 充值", "Beatra 控制台充值 starter ¥29 = 11,000 credits"),
      ("🖼️ 收素材", "hero 相 + 食材相（已收 AI 圖，建議補實物照）"),
      ("🎬 render", "image_to_video：seedance-2-mini 720p / 16:9 / 15秒"),
      ("📤 出片", "約 5,550 credits → 輸出 MP4"),
    ],
    "note":"🎥 產品：芝士番茄鮮肉餃。授權至 ~09-09。比例未最終確認（16:9/1:1/9:16）。"
  },
  {
    "slug":"patrol", "title":"每日自動巡檢",
    "code":"巡查 / CDM 跑咗未",
    "steps":[
      ("⏰ 21:40 cron", "自動跑 cdm_check_today.py"),
      ("🔍 查 marker", "確認今晚 CDM 跑咗未（target=今日+2）"),
      ("📁 查輸出", "輸出目錄 PDF 齊唔齊（執貨表+發票）"),
      ("📲 微信 report", "結果自動 send 去你微信"),
    ],
    "note":"🤖 呢張卡本身嘅即時狀態都會顯示喺首頁「即時狀態」卡。"
  },
]

TPL = '''<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#0a0e14">
<title>{title} · 小Q工作台</title>
<style>
:root{{--bg:#0a0e14;--card:#151b24;--line:#26303d;--txt:#e6edf3;--sub:#8b97a7;--cyan:#00e5ff;--purple:#b388ff;--green:#00e676;--orange:#ff6b35}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang HK","Microsoft JhengHei",sans-serif;padding:16px;max-width:680px;margin:0 auto;line-height:1.5}}
header{{display:flex;align-items:center;gap:12px;margin-bottom:18px}}
header a{{color:var(--cyan);text-decoration:none;font-size:.82rem;background:var(--card);border:1px solid var(--line);padding:6px 12px;border-radius:8px}}
header h1{{font-size:1.15rem;font-weight:700}}
.code{{display:inline-block;background:rgba(0,229,255,.12);color:var(--cyan);font-size:.72rem;padding:2px 9px;border-radius:6px;font-family:ui-monospace,Menlo,monospace;margin-bottom:14px}}
.flow{{display:flex;flex-direction:column;gap:0}}
.step{{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--cyan);border-radius:12px;padding:14px;display:flex;gap:12px;align-items:flex-start}}
.step .num{{flex:0 0 30px;height:30px;border-radius:50%;background:linear-gradient(135deg,var(--cyan),var(--purple));color:#0a0e14;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:.9rem}}
.step .t{{font-weight:600;font-size:.92rem;margin-bottom:3px}}
.step .d{{font-size:.8rem;color:var(--sub)}}
.arrow{{text-align:center;color:var(--purple);font-size:1.2rem;margin:2px 0;padding-left:14px}}
.note{{margin-top:20px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px;font-size:.8rem;color:var(--sub)}}
.note b{{color:var(--orange)}}
</style></head>
<body>
<header><a href="../index.html">← 工作台</a><h1>{title}</h1></header>
<div class="code">口令：{code}</div>
<div class="flow">
{steps}
</div>
<div class="note">{note}</div>
</body></html>'''

for f in FLOWS:
    steps_html = ""
    for i, s in enumerate(f["steps"], 1):
        block = ('<div class="step"><div class="num">{i}</div><div><div class="t">{t}</div><div class="d">{d}</div></div></div>').format(i=i, t=s[0], d=s[1])
        steps_html += block
        if i < len(f["steps"]):
            steps_html += '<div class="arrow">↓</div>'
    html = TPL.format(title=f["title"], code=f["code"], steps=steps_html, note=f["note"])
    path = os.path.join(OUT, f["slug"] + ".html")
    open(path, "w", encoding="utf-8").write(html)
    print("生成:", f["slug"] + ".html", "(%d 步)" % len(f["steps"]))
print("全部流程頁完成，共 %d 個" % len(FLOWS))
