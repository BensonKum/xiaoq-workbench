# -*- coding: utf-8 -*-
# 小Q工作台 自動更新：寫 status.json + push 上 GitHub Pages
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
    # 1) 生成 status.json
    run([PY, os.path.join(BASE, "gen_status.py")])
    # 2) git push（remote 已含 token）
    run(["git", "-C", BASE, "add", "status.json"])
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    run(["git", "-C", BASE, "commit", "-m", "自動更新 status.json %s" % now])
    run(["git", "-C", BASE, "push"])
    print("✅ 小Q工作台已更新並推送")

if __name__ == "__main__":
    main()
