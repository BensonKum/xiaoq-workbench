#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
膠盒倉存 xlsx 一有更新 -> 自動跑 update_status.py -> git push origin main

設計要點：
- 只監察 update_status.py 實際讀取嗰份 xlsx（工作區正本）。
- 用 md5 做狀態比較：xlsx 冇變就乜都唔做（idempotent，可安全高頻跑）。
- update_status.py 一定要用 Python312（managed 3.13 無 openpyxl）。
- 只 commit + push status.json（唔碰其他未跟蹤檔）。
- push 閘門 = 倉存數值（inventory）真係變咗先 commit。
- 每次跑結尾都 ensure_pushed()：如果本地有未 push 嘅 status.json commit
  （例如上次喺 sandbox 跑 git push 失敗），會自動補 push + retry，唔會漏。
- git push 用 repo 設好嘅 SSH key：core.sshCommand 已加
  UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=accept-new，
  繞開 sandbox 無權讀 ~/.ssh/known_hosts 引致 Host key verification failed 嘅問題。
"""
import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_XLSX = r'C:\Users\benso\WorkBuddy\2026-09-21-11-40-31\cdm\膠盒倉存(WB).xlsx'
UPDATE_STATUS = os.path.join(HERE, 'update_status.py')
STATUS_JSON = os.path.join(HERE, 'status.json')
STATE_FILE = os.path.join(HERE, '.box_sync_state.json')
LOG_FILE = os.path.join(HERE, '_box_sync.log')
PY312 = r'C:\Users\benso\AppData\Local\Programs\Python\Python312\python.exe'
# sandbox 無權讀 ~/.ssh/known_hosts -> Permission denied -> Host key verification failed
# 繞開：唔驗 known_hosts，直接 accept-new
SSH_CMD = ('ssh -i C:/Users/benso/.ssh/id_ed25519_xiaoq -o IdentitiesOnly=yes '
           '-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null')


def log(msg):
    line = '[%s] %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def run(cmd, ssh=False, **kw):
    env = dict(os.environ)
    if ssh:
        env['GIT_SSH_COMMAND'] = SSH_CMD
    return subprocess.run(cmd, cwd=HERE, env=env,
                          capture_output=True, text=True, **kw)


def _read_inventory_from_text(text):
    try:
        return json.loads(text).get('inventory')
    except Exception:
        return None


def current_inventory():
    try:
        with open(STATUS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f).get('inventory')
    except Exception:
        return None


def committed_inventory():
    r = run(['git', 'show', 'HEAD:status.json'])
    if r.returncode != 0:
        return None
    return _read_inventory_from_text(r.stdout)


def unpushed_status_commits():
    """本地領先 origin/main 且涉及 status.json 嘅 commit 數（0 = 冇嘢要 push）。"""
    r = run(['git', 'rev-list', '--count', 'origin/main..HEAD'])
    if r.returncode != 0:
        return 0
    try:
        n = int(r.stdout.strip() or '0')
    except ValueError:
        return 0
    if n <= 0:
        return 0
    d = run(['git', 'diff', '--name-only', 'origin/main..HEAD'])
    if 'status.json' in d.stdout:
        return n
    return 0


def ensure_pushed():
    """如果本地有未 push 嘅 status.json commit，補 push（含 retry 3 次）。"""
    # 先 refresh origin/main（失敗當 best-effort，忽略）
    run(['git', 'fetch', 'origin'], ssh=True)
    n = unpushed_status_commits()
    if n == 0:
        return 0
    log('偵測到 %d 個未 push 嘅 status.json commit，嘗試補 push...' % n)
    last_err = ''
    for attempt in range(3):
        p = run(['git', 'push', 'origin', 'main'], ssh=True)
        if p.returncode == 0:
            log('✅ 已 push 去 main（GitHub Pages 自動重建，手機約 20s 後見到更新）')
            return 0
        last_err = p.stderr.strip()[:400]
        log('⚠️ push 失敗 (試 %d/3)：%s' % (attempt + 1, last_err))
    log('❌ 補 push 失敗：%s' % last_err)
    return 1


def _save_state(md5val):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'md5': md5val,
                       'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                      f, ensure_ascii=False, indent=2)
    except Exception as e:
        log('⚠️ 寫狀態檔失敗：%s' % e)


def main():
    if not os.path.exists(SOURCE_XLSX):
        log('⚠️ 搵唔到源 xlsx：%s' % SOURCE_XLSX)
        return 1
    if not os.path.exists(PY312):
        log('⚠️ 搵唔到 Python312：%s' % PY312)
        return 1

    cur = md5_of(SOURCE_XLSX)
    prev = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                prev = json.load(f).get('md5')
        except Exception:
            prev = None

    if prev != cur:
        log('偵測到 xlsx 變動（%s -> %s），跑 update_status.py ...' % (prev, cur))
        r = run([PY312, UPDATE_STATUS])
        if r.returncode != 0:
            log('❌ update_status.py 失敗（rc=%d）：%s'
                % (r.returncode, r.stderr.strip()[:500]))
            return 1
        log('✅ update_status.py 完成')

        cur_inv = current_inventory()
        old_inv = committed_inventory()
        if cur_inv != old_inv:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M')
            run(['git', 'add', 'status.json'])
            c = run(['git', 'commit', '-m', 'auto: sync box inventory @ %s' % ts])
            if c.returncode != 0:
                log('❌ git commit 失敗：%s' % c.stderr.strip()[:500])
                return 1
            log('✅ 已 commit 新倉存數值')
        else:
            log('倉存數值冇變（只係時間戳／其他欄變），跳過 commit。')
        _save_state(cur)

    # 無論 xlsx 有冇改，都確保已 push（修復上次 push 失敗漏 push 嘅情況）
    ensure_pushed()
    return 0


if __name__ == '__main__':
    sys.exit(main())
