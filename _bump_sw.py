#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同步版本號：index.html 嘅 APP_VERSION <-> sw.js 嘅 APP_VER
用法：
    python _bump_sw.py            # 修改後 --check 過就寫入
    python _bump_sw.py --check    # 只校驗，有差距就回傳碼 1
每次改完 index.html 要 deploy 之前跑一次。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, 'index.html')
SW = os.path.join(HERE, 'sw.js')

RE_HTML = re.compile(r"var APP_VERSION\s*=\s*'([^']+)'")
RE_SW = re.compile(r"const APP_VER\s*=\s*'([^']+)'")


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def main():
    check_only = '--check' in sys.argv
    html = read(HTML)
    sw = read(SW)

    m_html = RE_HTML.search(html)
    m_sw = RE_SW.search(sw)
    if not m_html:
        print('✗ index.html 搵唔到 var APP_VERSION')
        return 1
    if not m_sw:
        print('✗ sw.js 搵唔到 const APP_VER')
        return 1

    ver = m_html.group(1)
    sw_ver = m_sw.group(1)
    state = '✅ 一致' if ver == sw_ver else '⚠️ 有差距'
    print('index.html APP_VERSION = %s' % ver)
    print('sw.js     APP_VER      = %s' % sw_ver)
    print('狀態：%s' % state)

    if check_only:
        return 0 if ver == sw_ver else 1

    if ver != sw_ver:
        new_sw = RE_SW.sub(lambda _: "const APP_VER = '%s'" % ver, sw, count=1)
        tmp = SW + '.tmp'
        with io.open(tmp, 'w', encoding='utf-8', newline='') as f:
            f.write(new_sw)
        os.replace(tmp, SW)
        print('→ 已把 sw.js 寫成 %s' % ver)

    # 順便驗一腳：sw.js 入面嘅 CACHE 名要寫成動態跟 APP_VER
    sw2 = read(SW)
    cache_ok = re.search(r"const CACHE\s*=\s*'xq-workbench-'\s*\+\s*APP_VER", sw2) is not None
    print('CACHE 名 = xq-workbench- + APP_VER（動態）：%s' % ('✅' if cache_ok else '❌ 要改做動態拼接'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
