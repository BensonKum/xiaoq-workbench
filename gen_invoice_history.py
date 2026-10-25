#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate static invoice_history.json from CDM Flow1 單日發票 (inv_DD-MM-YYYY.xlsx).

目的：雲端／手機版嘅「CDM 發票總額 整月走勢」唔使靠本機 API（localhost:8083），
      改讀同源靜態 invoice_history.json（deploy 時一齊上）。本機版仍可用 API 取 live 數據。

用法：
  python gen_invoice_history.py        # 生成 invoice_history.json
"""
import json
import os
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import api  # 重用 read_invoice_history()


def main():
    all_m = api.read_invoice_history()['months']
    by_month = {}
    for m in all_m:
        d = api.read_invoice_history(m)
        by_month[m] = {
            'month': d['month'],
            'rows': d['rows'],
            'updated_at': d.get('updated_at', ''),
        }
    out = {
        'generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'months': all_m,
        'by_month': by_month,
    }
    out_path = os.path.join(HERE, 'invoice_history.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    n = sum(len(v['rows']) for v in by_month.values())
    print('✅ invoice_history.json 生成：%d 個月 / %d 日資料 → %s' % (len(all_m), n, out_path))


if __name__ == '__main__':
    main()
