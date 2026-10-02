# -*- coding: utf-8 -*-
# 生成 xiaoq-workbench/status.json（小Q工作台即時狀態）
# 用：python gen_status.py   → 寫入同目錄 status.json
import os, json, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
CDM_DIR = r"C:\Users\user\Desktop\QClaw\CDM(發票及執貨表)"
STATE_FILE = os.path.join(BASE, "_state.json")  # 記錄 sync products / deploy 日期

def load_state():
    if os.path.exists(STATE_FILE):
        try: return json.load(open(STATE_FILE, encoding="utf-8"))
        except: pass
    return {}

def cdm_status():
    now = datetime.datetime.now()
    target = (now + datetime.timedelta(days=2)).strftime("%Y%m%d")
    marker = os.path.join(CDM_DIR, ".last_processed.txt")
    marker_val = open(marker, encoding="utf-8").read().strip() if os.path.exists(marker) else ""
    out_dir = os.path.join(CDM_DIR, "錢大媽發票及執貨表_%s" % target)
    ran = (marker_val == target) and os.path.exists(out_dir)
    files = []
    pdf_ready = False
    if os.path.exists(out_dir):
        pdfs = [f for f in os.listdir(out_dir) if f.lower().endswith(".pdf")]
        pick = [f for f in pdfs if "執貨入箱表" in f and target in f]
        inv = [f for f in pdfs if "錢大媽發票" in f and (now+datetime.timedelta(days=2)).strftime("%d%m%Y") in f]
        pdf_ready = bool(pick and inv)
        for p in sorted(pdfs):
            files.append({"name": p, "size_kb": os.path.getsize(os.path.join(out_dir, p))//1024})
    return {"ran_today": ran, "target_date": target, "pdf_ready": pdf_ready, "files": files}

def main():
    st = load_state()
    now = datetime.datetime.now()
    data = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "cdm": cdm_status(),
        "firestore": {
            "products_synced_date": st.get("products_synced_date", "2026-09-11"),
            "products_count": st.get("products_count", 114)
        },
        "todos": [
            {"text":"清 Firestore /products security rule（allow read:if true 係暫行）", "done": False},
            {"text":"YM808/YM809 換實物相（local_img 仍佔位圖）", "done": False},
            {"text":"CDM email 加 inamyleung 後備收件人（現寫死只去 bensonkum86）", "done": False},
            {"text":"桌面整理 3 個 _desktop版 取捨 + TERRY 4 夾合併", "done": False},
            {"text":"Gmail App Password 硬編碼風險（cdm_auto.py）", "done": False},
            {"text":"Beatra 充值 ¥29 後 render 15 秒廣告片", "done": False}
        ]
    }
    out = os.path.join(BASE, "status.json")
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("status.json 已寫入:", out)
    print("  CDM ran_today=%s pdf_ready=%s target=%s" % (data["cdm"]["ran_today"], data["cdm"]["pdf_ready"], data["cdm"]["target_date"]))

if __name__ == "__main__":
    main()
