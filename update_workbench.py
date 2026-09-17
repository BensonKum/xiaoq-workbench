# -*- coding: utf-8 -*-
# 小Q工作台 自動更新：寫 status.json + 重建流程頁 + push 上 GitHub Pages
import subprocess, os, datetime, sys
# 強制 stdout UTF-8（PowerShell cp950 會爆）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Program Files\QClaw\v0.2.37.630\resources\openclaw\config/bin/python/python.cmd"

def run(cmd):
    print(">>>", " ".join(cmd))
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout:
        print(r.stdout.strip())
    if r.stderr:
        print("[stderr]", r.stderr.strip())
    if r.returncode != 0:
        raise SystemExit("命令失敗: " + " ".join(cmd))
    return r

def main():
    # 0) 重建 8 個流程可視頁 (workflows/*.html)
    run([PY, os.path.join(BASE, "gen_workflows.py")])
    # 1) 生成 status.json（讀本地 CDM 資料）
    run([PY, os.path.join(BASE, "gen_status.py")])
    # 2) git add + commit + push（remote 已含 token）
    run(["git", "-C", BASE, "add", "status.json", "workflows/"])
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # 冇變更就唔 commit（git commit 會報错）
    diff = subprocess.run(["git", "-C", BASE, "diff", "--cached", "--quiet"],
                          capture_output=True, text=True)
    if diff.returncode != 0:
        run(["git", "-C", BASE, "commit", "-m", "自動更新 工作台 %s" % now])
        run(["git", "-C", BASE, "push"])
        print("✅ 小Q工作台已更新並推送")
    else:
        print("ℹ️ 無變更，跳過推送")

if __name__ == "__main__":
    main()
