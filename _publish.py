#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish 前自動升版本號 —— 用手嘅「 publish 工作台 」流程第一步唯一指令。

做咩：
  1. 讀 index.html 嘅 APP_VERSION（例 v39）→ 解析出數字
  2. 如有需要，對齊線上版本（online 若比本地高，就以 online 為準再 +1，防「本地落後 publish 咗新嘅」）
  3. 寫返 index.html 同 sw.js（--dry 只打印唔落檔）
  4. git commit（--no-commit 可 skip）

用法：
  python _publish.py                # 升版 + 落檔 + commit（正常用呢個）
  python _publish.py --dry          # 只打印會升到邊，唔改檔案
  python _publish.py --no-commit    # 升版落檔，但唔 commit
  python _publish.py --check        # 純校驗（index.html ↔ sw.js 一致），exit 1 = 有差距

做完之後：助手會 redeploy（連結不變），手機撳左下橙色「⟳ 檢查更新」就Update到新版。
"""
import io
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, 'index.html')
SW = os.path.join(HERE, 'sw.js')

RE_HTML = re.compile(r"(var APP_VERSION\s*=\s*)'([^']+)'")
RE_SW = re.compile(r"(const APP_VER\s*=\s*)'([^']+)'")

ONLINE = 'https://xiaoq-workbench-76614.app.workbuddy.host/index.html'


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def num(v):
    m = re.search(r'(\d+)', v or '')
    return int(m.group(1)) if m else 0


def bump(v):
    return 'v%d' % (num(v) + 1)


def online_ver():
    try:
        with urllib.request.urlopen(ONLINE, timeout=15) as r:
            html = r.read().decode('utf-8', 'ignore')
        m = RE_HTML.search(html)
        return m.group(2) if m else None
    except Exception as e:                                # 無網／線上掛咗都唔好阻住升版
        print('  ⚠️ 讀唔到線上版本（%s），一律照本地升版' % type(e).__name__)
        return None


def main():
    args = sys.argv[1:]
    dry = '--dry' in args
    no_commit = '--no-commit' in args

    if '--check' in args:                                  # 純校驗模式
        h = RE_HTML.search(read(HTML))
        s = RE_SW.search(read(SW))
        ok = bool(h and s and h.group(2) == s.group(1))
        print('index.html=%s | sw.js=%s → %s' % (
            h.group(2) if h else '?', s.group(1) if s else '?',
            '✅ 一致' if ok else '❌ 唔一致'))
        return 0 if ok else 1

    html = read(HTML)
    sw = read(SW)
    m_h = RE_HTML.search(html)
    m_s = RE_SW.search(sw)
    if not m_h or not m_s:
        print('✗ 搵唔到版本號（index.html 要 var APP_VERSION、sw.js 要 const APP_VER）')
        return 1

    old = m_h.group(2)
    new = bump(old)

    ov = online_ver()
    if ov and num(ov) >= num(old):
        if num(ov) > num(old):
            new = bump(ov)
            print('線上係 %s（本地 %s），本地落後 → 升做 %s' % (ov, old, new))
        else:
            print('線上同本地都係 %s，直接升做 %s' % (old, new))

    print('%s → %s%s' % (old, new, '（--dry，未落檔）' if dry else ''))
    if dry:
        return 0

    html2 = RE_HTML.sub(lambda m: m.group(1) + "'%s'" % new, html, count=1)
    sw2 = RE_SW.sub(lambda m: m.group(1) + "'%s'" % new, sw, count=1)

    tmp = HTML + '.tmp'
    write(tmp, html2)
    os.replace(tmp, HTML)
    tmp = SW + '.tmp'
    write(tmp, sw2)
    os.replace(tmp, SW)

    cached = ('xq-workbench-') in sw2 and ('+ APP_VER' in sw2)
    print('✓ index.html / sw.js 已寫成 %s（CACHE 動態跟 APP_VER：%s）'
          % (new, '✅' if cached else '❌ 要改做 \'xq-workbench-\' + APP_VER'))

    if not no_commit:
        os.system('git add -A && git -c user.name=Benson -c user.email=benso@local '
                  'commit -q -m "%s auto-bump by _publish.py"' % new)
        print('✓ 已 git commit（本地）')

    print('→ 可以 publish 了；publish 完用手機撳左下「⟳ 檢查更新 %s」' % new)
    return 0


if __name__ == '__main__':
    sys.exit(main())
