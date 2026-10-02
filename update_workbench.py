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
PY = r"C:\Users\user\.workbuddy\binaries\python\versions\3.13.12\python.exe"

def run(cmd):
    print(">>>", " ".join(cmd))
    # 停用互動式帳密輸入，避免憑證助手彈窗令 cron 卡死
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
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
        # push：本環境可能封鎖 github 出站，加 timeout 唔好 hang 死 cron/自動化
        print(">>> git push (timeout 60s)")
        env = dict(os.environ); env["GIT_TERMINAL_PROMPT"] = "0"; env["GCM_INTERACTIVE"] = "never"
        try:
            pr = subprocess.run(["git", "-C", BASE, "push"], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", env=env, timeout=60)
            if pr.returncode == 0:
                print("✅ 小Q工作台已更新並推送")
            else:
                print("[warn] 本地已更新並 commit，但 push 失敗 (rc=%d)" % pr.returncode)
                if pr.stderr: print("  ", pr.stderr.strip()[:300])
                print("  → 請喺有網絡嘅機手動：`git -C %s push`" % BASE)
        except subprocess.TimeoutExpired:
            print("[warn] push 超時（本環境或封鎖 github 出站），本地已更新並 commit")
            print("  → 請喺有網絡嘅機手動：`git -C %s push`" % BASE)
    else:
        print("ℹ️ 無變更，跳過推送")

if __name__ == "__main__":
    main()
