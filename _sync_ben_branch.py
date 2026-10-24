#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_sync_ben_branch.py — Owner（benso 部機）專用：由 contributor（user 部機）嘅
`ben/workbench` 挑選「有功能價值」嘅 commit  cherry-pick 落 `main`。

💡 為何唔係「定期 merge --no-ff」：
   ben/workbench 上嘅 commit 95% 係本地自動化產物（status.json 每日重生 +
   update_workbench.py）。呢兩樣嘅唯一源都係 owner 部機，merge 落 main 之後
   又要全數覆返 owner 版 = 空 merge，只會把 conflict 帶入 main（寫死舊數 = 零容忍）。
   所以正確做法係「按需 cherry-pick 功能欄」。

鐵規（不可違）：
  1. status.json 唯一源 = 本機 update_status.py → 本腳本**永唔** merge / cherry-pick status.json。
  2. 只處理白名單（功能檔）；黑名單（本地自動化 noise）一律 skip 並報告。
  3. 衝突即停手、回滾、報告 Benson；絕不 --force、絕不 push。
  4. 第二部機（user 部機）唔喺本腳本視野內，本腳本只碰本機 repo。

用法：
  python _sync_ben_branch.py            # 只讀報告（默認 dry-run）
  python _sync_ben_branch.py --apply    # 逐個 cherry-pick 白名單 commit
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
BRANCH_OTHER = 'ben/workbench'
BRANCH_OWN = 'main'

# 白名單：咭 commit 有呢啲檔變動，先至值得 cherry-pick 落 main
WHITELIST = (
    'index.html',
    'sw.js',
    'manifest.json',
    'update_status.py',
    'api.py',
    '_publish.py',
    '.github/workflows/deploy.yml',
    'icon-192.png',
    'icon-512.png',
    'apple-touch-icon.png',
    'favicon-32.png',
)

# 黑名單：本地自動化 noise，永唔碰
BLACKLIST = (
    'status.json',
    'update_workbench.py',
    '__pycache__',
    '.pyc',
)


def run(cmd, check=True):
    p = subprocess.run(cmd, cwd=REPO, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    if check and p.returncode != 0:
        raise SystemExit('❌ 指令失敗：%s\n%s\n%s' % (' '.join(cmd), p.stdout, p.stderr))
    return p.returncode, p.stdout, p.stderr


def current_branch():
    _, out, _ = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    return out.strip()


def changed_files(sha):
    rc, out, _ = run(['git', 'show', '--name-only', '--format=', sha], check=False)
    if rc != 0:
        return []
    return [f.strip() for f in out.splitlines() if f.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='真剔 cherry-pick（默認只讀）')
    args = ap.parse_args()

    print('=' * 62)
    print('_sync_ben_branch.py — Owner side 挑選 ben/workbench 嘅功能 commit')
    print('=' * 62)

    cur = current_branch()
    print('本機分支：%s' % cur)
    if cur != BRANCH_OWN:
        print('⚠️  要喺 %s 上先至 cherry-pick（而家係 %s）。\n'
              '    如要用 apply：git checkout %s' % (BRANCH_OWN, cur, BRANCH_OWN))

    print('\n[1] fetch origin %s ...' % BRANCH_OTHER)
    run(['git', 'fetch', 'origin', BRANCH_OTHER])
    print('    ✅ 完成')

    rc, out, _ = run(['git', 'rev-list', '--reverse', '--oneline',
                      '%s..origin/%s' % (BRANCH_OWN, BRANCH_OTHER)], check=False)
    if rc != 0 or not out.strip():
        print('\n✅ 冇新 commit，%s 落 뒤 %s（已同步）。' % (BRANCH_OTHER, BRANCH_OWN))
        return 0
    commits = [l.split(maxsplit=1)[0] for l in out.strip().splitlines() if l.strip()]
    print('    待處理 commit：%d 個' % len(commits))

    print('\n[2] 逐個 commit 分類 ...')
    candidates, noisy = [], []
    for sha in commits:
        rc, subj, _ = run(['git', 'log', '-1', '--format=%s', sha], check=False)
        files = changed_files(sha)
        hit_w = [f for f in files if f in WHITELIST]
        hit_b = [f for f in files if any(b in f for b in BLACKLIST)]
        if hit_w:
            candidates.append((sha, subj.strip(), hit_w, hit_b))
        else:
            noisy.append((sha, subj.strip(), hit_b or files))

    for sha, subj, files, _b in candidates:
        print('    ⭐ %s %s' % (sha, subj))
        print('       功能檔：%s' % ', '.join(files))
    for sha, subj, files in noisy:
        print('    ⏭  %s %s' % (sha, subj))
        print('       跳過（淨係本地自動化 noise）：%s' % ', '.join(files[:4]))

    total_w = sum(len(c[2]) for c in candidates)
    if not candidates:
        print('\n✅ %s 上面全部 %d 個 commit 都係本地 noise，'
              '對 %s 零淨價值 → 唔使 cherry-pick，兩邊各自向前走就得。'
              % (BRANCH_OTHER, len(commits), BRANCH_OWN))
        print('    （GitHub 備份目的已經達到：%s 上面有呢 %d 個 commit。）'
              % (BRANCH_OTHER, len(commits)))
        return 0

    print('\n[3] 總結：%d 個 commit 含功能檔（共 %d 個檔）值得 cherry-pick 落 %s'
          % (len(candidates), total_w, BRANCH_OWN))
    if not args.apply:
        print('\n🧪 --dry-run（默認）：未有改任何嘢。')
        print('   要真剔cherry-pick：python _sync_ben_branch.py --apply')
        return 0

    if cur != BRANCH_OWN:
        print('❌ 而家唔喺 %s 分支，拒絕 apply。' % BRANCH_OWN)
        return 2

    print('\n[4] 逐個 cherry-pick ...')
    for sha, subj, files, hit_b in candidates:
        if hit_b:
            print('    ⚠️  %s 同時改咗黑名單檔 %s → 跳過，保護 status.json 唯一源'
                  % (sha, ', '.join(hit_b)))
            continue
        print('    ⭐ cherry-pick %s %s ...' % (sha, subj))
        rc, o, e = run(['git', 'cherry-pick', sha], check=False)
        if rc != 0:
            print('       ❌ 衝突／失敗 → 回滾（cherry-pick --abort），停手等 Benson 處理')
            run(['git', 'cherry-pick', '--abort'], check=False)
            print('    ❌ 已停手。手動：git status 睇清楚再決定。')
            return 1
        print('       ✅ 完成')
        # 雙保險：cherry-pick 後強制還原 status.json 為本機版
        run(['git', 'checkout', '%s' % BRANCH_OWN, '--', 'status.json'], check=False)
        rc2, diff, _ = run(['git', 'diff', '--name-only', 'HEAD', 'origin/%s' % BRANCH_OTHER], check=False)

    print('\n✅ cherry-pick 完成。記住跟 publish 三步：')
    print('    python _publish.py  →  git push origin main  →  sites deploy')
    print('    （呢個腳本本身唔 push、唔 deploy。）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
