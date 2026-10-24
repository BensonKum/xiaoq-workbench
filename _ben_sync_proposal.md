# 給 user 部機（C:\Users\user\.qclaw\workspace\xiaoq-workbench）嘅修改建議

**目的**：凍結 `status.json` 喺 `ben/workbench` branch 上（保持 `1a47ffc`），令 owner 唔使再 merge 佢（owner 版 `status.json` 係唯一源，兩邊各出一版一定會衝突）。

---

## 關鍵發現

**Benso 部機嘅版本（`Claw\tools-hub\update_status.py`）** 與 **User 部機嘅版本（`gen_status.py`）** 係兩條唔通嘅代碼路徑，生成嘅 JSON 結構亦唔完全一樣 —— 即係「兩邊各自 generate」本質就會 conflict。所以凍結 = 最乾淨解法。

---

## 具體修改（`update_workbench.py`）

將原本嘅三段式改成 **「只更新 workflow HTML、status.json 睇住唔推」**：

```python
# === 原代碼（會有問題）===
def main():
    # 0) 重建 8 個流程可視頁
    run([PY, os.path.join(BASE, "gen_workflows.py")])
    # 1) 生成 status.json（讀本地 CDM 資料）
    run([PY, os.path.join(BASE, "gen_status.py")])          ← 呢行要刪 / 改
    # 2) git add + commit + push
    run(["git", "-C", BASE, "add", "status.json", "workflows/"])  ← 要去掉 status.json
    # ... commit + push 跟住行 ...
```

```python
# === 建議新代碼 ===
def main():
    # 0) 重建 8 個流程可視頁（呢個仲要，因為係 user 部機本地展示用）
    run([PY, os.path.join(BASE, "gen_workflows.py")])
    
    # 1) 【改】唔再生成 status.json；只保留本地一份最新
    #    gen_status.py 照跑（user 部機嘅本地 workbench 仍要看 status），
    #    但唔好 add 落 git，唔好 push 落 branch。
    #    —— 這樣 user 部機本地顯示正常，GitHub 備份唔會與 benso 衝突
    run([PY, os.path.join(BASE, "gen_status.py")])
    
    # 2) 【改】只 add  workflow HTML，唔 add status.json
    run(["git", "-C", BASE, "add", "workflows/"])
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    diff = subprocess.run(
        ["git", "-C", BASE, "diff", "--cached", "--quiet"],
        capture_output=True, text=True
    )
    if diff.returncode != 0:
        run(["git", "-C", BASE, "commit", "-m", "自動更新 工作台 %s" % now])
        run(["git", "-C", BASE, "push"])
    else:
        print("ℹ️ 無變更，跳過推送")
```

---

## 要點解釋

| 項目 | 原行為 | 建議行為 | 點解 |
|---|---|---|---|
| `gen_status.py` 執行 | 執行 + add + push | **執行但不 stage** | user 部機本地 workbench 仍然要看 status，本地顯示唔可以損 |
| `status.json` git add | add 埋 | **唔 add** | 保留 `1a47ffc` 凍結版，owner 永遠唔需要 merge 佢 |
| `workflows/*.html` | 正常 commit + push | **照舊** | 呢啲係 user 部機本地展示用，owner 冇用 |

---

## 凍結之後會點？

- **GitHub 備份**：`ben/workbench` branch 上面嘅 `status.json` 永遠停喺 `1a47ffc` 嗰版，唔變。
- **Benso owner 部機**：自己 `update_status.py` 出 status.json，push `main`，兩邊唔撞。
- **Owner merge 時機**：當 user 部機真正有新的功能檔要合入（例如新 workflow HTML、新腳本），佢先 commit 落 `ben/workbench`，owner 再用 `_sync_ben_branch.py` 按需 cherry-pick。日常自動化只處理 workflows、唔碰 status.json。

---

## 額外安全閥（建議加）

喺 `update_workbench.py` 頂頭加一行提醒，每當自動化跑時印出提示：

```python
# ⚠️ 鐵規：status.json 唔好 push 落 branch，由 benso 部機唯一源控制
# 改咗呢行會令 benso 部機嘅 merge 永遠 conflict，請先同 Benson 溝通
if 'status.json' in sys.argv:
    raise SystemExit("唔好通過 command line 傳 status.json 入 push")
```

其實最直接的做法係 **唔好 add 住 status.json**（即上面建議），唔洗多餘 code。

---

## 測試清單

改完 run 一次，確認以下四項：

1. `git log --oneline -3 ben/workbench` → 新增一個 commit（只包含 `workflows/*.html`，唔包含 `status.json`）
2. `git show --stat HEAD` → 列出 `workflows/` 下嘅檔案，`status.json` 唔在名單
3. `git log --oneline main..origin/ben/workbench` → 所有 commit 都唔含 `status.json`
4. User 部機本地打開 `index.html` 搵頂部 chip，status 仲顯示得（因為本地 `status.json` 仍然 regenerate）

---

## 如果 user 部機想保留 status.json 最新

另一選擇：**將 status.json 改名**（例如 `status.local.json`），唔叫 `status.json`，這樣就唔會與 benso 版衝突 —— 但代價係 benso 部機要改讀呢個新檔名。不如凍結簡單。

---

*此文件由 benso 部機生成，俾 user 部機同事參考用。唔使照抄，可隨需要調整。*
