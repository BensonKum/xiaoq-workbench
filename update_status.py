#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
祐興工作台狀態生成器
讀取本地數據，生成 status.json 上傳到 GitHub Pages
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 路徑配置
ONE_DRIVE_CDM = r'C:\Users\benso\OneDrive\Desktop\CDM'
WORKSPACE_CDM = r'C:\Users\benso\WorkBuddy\2026-09-21-11-40-31\cdm'
OUTPUT_FILE = r'C:\Users\benso\WorkBuddy\Claw\tools-hub\status.json'

def get_inventory_data():
    """讀取膠盒倉存數據（同一套邏輯 as api.py：當月 sheet + 最新有日期嗰行 + col6/col7）

    🚨 2026-10-03 修：舊 code 直接用 ws.max_row，10 月頁個 max_row 係「總用量」
       摘要行 → 讀到 0／None，而 status.json 又係手改過嘅舊值，
       搞到頂部 chip（/api/inventory）同流程卡（status.json）顯示唔一致。
    """
    inventory_file = os.path.join(WORKSPACE_CDM, '膠盒倉存(WB).xlsx')
    if not os.path.exists(inventory_file):
        return {'small': 0, 'big': 0, 'date': '未知'}

    try:
        # 直接用 api.py 既 read_box_latest，兩邊同源唔會再分歧
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import api
        box = api.read_box_latest(inventory_file)
        return {'small': box['small'], 'big': box['big'], 'date': box['date']}
    except Exception as e:
        print(f'讀取倉存失敗: {e}')

    return {'small': 0, 'big': 0, 'date': '未知'}

def get_cdm_status():
    """檢查 CDM 執貨表現狀"""
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    yesterday_str = (today - timedelta(days=1)).strftime('%Y%m%d')
    
    status = {
        'ran_today': False,
        'target_date': '',
        'pdf_ready': False,
        'invoice_ready': False,
        'files': []
    }
    
    # 檢查昨天和今天的執貨表
    for date_check in [yesterday_str, today_str]:
        folder = os.path.join(ONE_DRIVE_CDM, f'錢大媽發票及執貨表_{date_check}')
        if os.path.exists(folder):
            files = os.listdir(folder)
            has_pdf = any('delivery' in f and f.endswith('.pdf') for f in files)
            has_xlsx = any('delivery' in f and f.endswith('.xlsx') for f in files)
            
            status['files'].append({
                'date': date_check,
                'has_pdf': has_pdf,
                'has_xlsx': has_xlsx,
                'folder': folder
            })
            
            if has_pdf and has_xlsx:
                status['ran_today'] = True
                status['target_date'] = date_check
                status['pdf_ready'] = True
    
    # 檢查 10 月發票
    oct_folder = os.path.join(ONE_DRIVE_CDM, 'CDM 發票對數', 'CDM 發票', '10 Oct 2026')
    if os.path.exists(oct_folder):
        files = os.listdir(oct_folder)
        inv_count = len([f for f in files if f.startswith('inv_') and f.endswith('.xlsx')])
        status['invoice_count'] = inv_count
        status['invoice_ready'] = inv_count > 0
    else:
        status['invoice_count'] = 0
        status['invoice_ready'] = False
    
    return status

def _md5(path):
    import hashlib
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def get_flow1_sync():
    """Flow 1 單日發票「三處一致性」（OneDrive 真帳 vs Claw 副本 vs 工作區副本）

    起因（2026-10-04 21:55）：shadow 一向淨係同步 .py、唔同步 outputs，
    每晚 Flow1 出完新票 Claw 就差一張，要靠人手 ls 先發現。10/04 起
    Flow1 出票後會自動 sync_shadow()，呢度就負責「 reporting 出嚟」——
    用手機工作台（status.json）一眼睇到有冇缺 / 唔一致，唔使再靠人。
    """
    now = datetime.now()
    MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    name = '%02d %s %d' % (now.month, MONTH_ABBR[now.month - 1], now.year)
    src = os.path.join(ONE_DRIVE_CDM, 'CDM 發票對數', 'CDM 發票', name)
    shadows = [
        (os.path.join(r'C:\Users\benso\WorkBuddy', 'Claw', 'cdm'), 'Claw 副本'),
        (r'C:\Users\benso\WorkBuddy\2026-09-21-11-40-31\cdm', '工作區副本'),
    ]
    out = {'folder': name, 'files': 0, 'missing': [], 'mismatch': [],
           'ok': True, 'checked_at': now.strftime('%H:%M')}
    if not os.path.isdir(src):
        return out
    files = sorted(f for f in os.listdir(src)
                   if f.startswith('inv_') and f.endswith('.xlsx'))
    out['files'] = len(files)
    for fn in files:
        m = _md5(os.path.join(src, fn))
        for base, label in shadows:
            dp = os.path.join(base, 'CDM 發票對數', 'CDM 發票', name, fn)
            if not os.path.exists(dp):
                out['missing'].append('%s ／ %s' % (fn, label))
                out['ok'] = False
            elif _md5(dp) != m:
                out['mismatch'].append('%s ／ %s' % (fn, label))
                out['ok'] = False
    return out


_MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _folder_files(base, rel):
    """回傳 (abs_path, [檔名])；目錄冇就 ([], [])"""
    p = os.path.join(base, rel) if rel else base
    if not os.path.isdir(p):
        return p, []
    return p, sorted(os.listdir(p))


def get_cdm_workflow():
    """CDM 全流程跟進表（實讀檔案系統，逐步出檔案名 + 落地路徑 + 狀態）

    起因（2026-10-04 22:30）Benson：「CDM 流程文件散佈混亂，想一張表由第一步開始，
    列明每個步驟嘅檔案名稱、路徑放在邊度，容易跟蹤。」

    每個 step 欄位：
      id / no / name / time / auto（自動定人手）/ script / artifact（輸出檔名通配）
      / path（簡化路徑）/ full（完整路徑）/ status（ok / pending / manual）
      / detail（人類-readable 補充）/ files（呢步實際掃到嘅檔名）
    """
    now = datetime.now()
    tgt = now + timedelta(days=2)          # CDM 铁规：target = 今日 + 2
    tgt_str = tgt.strftime('%Y%m%d')
    tgt_date = tgt.strftime('%Y-%m-%d')
    name = '%02d %s %d' % (now.month, _MONTH_ABBR[now.month - 1], now.year)

    CLAW_CDM = os.path.join(r'C:\Users\benso\WorkBuddy', 'Claw', 'cdm')
    WS_CDM = r'C:\Users\benso\WorkBuddy\2026-09-21-11-40-31\cdm'

    inv_rel = os.path.join('CDM 發票對數', 'CDM 發票', name)
    inv_full, inv_files = _folder_files(ONE_DRIVE_CDM, inv_rel)
    invs = [f for f in inv_files if f.startswith('inv_') and f.endswith('.xlsx')]
    invs_latest = invs[-1] if invs else ''

    steps = []

    # ① 訂單入庫（Yahoo 下載）
    odir, ofiles = _folder_files(ONE_DRIVE_CDM, '訂單')
    ym = tgt.strftime('%Y%m')            # 只計本月，唔好講全年歷史總數
    ords = [f for f in ofiles if f.upper().endswith('.XLS') and ym in f]
    steps.append({
        'id': 'w01', 'no': 1, 'name': '訂單入庫', 'time': '19:00', 'auto': False,
        'script': '（人類：Yahoo 下載祐興定單附件）',
        'artifact': '訂單\\{YYYYMMDD}*.XLS',
        'path': 'OneDrive\\Desktop\\CDM\\訂單\\',
        'full': odir, 'status': 'ok' if ords else 'pending',
        'detail': ('本月冇 .XLS 入到嚟（共 %d 個歷史 .XLS）' % len(ords)
                   ) if not ords else ('本月揾到 %d 個 .XLS' % len(ords)),
        'files': ords[-3:],
    })

    # ② 落單去重（Archive + processed_orders.json）
    arch, afiles = _folder_files(ONE_DRIVE_CDM, 'Archive')
    d_arch = [f for f in afiles if f.startswith('delivery_') and f.endswith('.xlsx')]
    d_arch_m = [f for f in d_arch if ym in f]
    pj = os.path.join(ONE_DRIVE_CDM, 'processed_orders.json')
    steps.append({
        'id': 'w02', 'no': 2, 'name': '落單去重', 'time': '19:35', 'auto': True,
        'script': '_cdm_common.py → Archive',
        'artifact': 'Archive\\delivery_{YYYYMMDD}.xlsx',
        'path': 'OneDrive\\Desktop\\CDM\\Archive\\',
        'full': arch, 'status': 'ok' if d_arch_m else 'pending',
        'detail': '本月 Archive %d 份 delivery_*（共 %d 份歷史）｜processed_orders.json %s'
                  % (len(d_arch_m), len(d_arch),
                     '存在' if os.path.exists(pj) else '唔喺度'),
        'files': d_arch_m[-3:] if d_arch_m else [],
    })

    # ③ 19:40 主流程 → 執貨表
    drel = '錢大媽發票及執貨表_%s' % tgt_str
    dfull, dfiles = _folder_files(ONE_DRIVE_CDM, drel)
    dwb = [f for f in dfiles if f.endswith('_wb.xlsx') or f.endswith('.pdf')]
    steps.append({
        'id': 'w03', 'no': 3, 'name': '19:40 主流程 · 執貨表', 'time': '19:40', 'auto': True,
        'script': 'gen_delivery.py',
        'artifact': '錢大媽發票及執貨表_{YYYYMMDD}\\delivery_{YYYYMMDD}_wb.xlsx + .pdf',
        'path': 'OneDrive\\Desktop\\CDM\\錢大媽發票及執貨表_{YYYYMMDD}\\',
        'full': dfull, 'status': 'ok' if dwb else 'pending',
        'detail': ('目標日 %s：輸出 %d 個檔' % (tgt_date, len(dwb))) if dwb
                  else ('目標日 %s：執貨表還未到（要等 target 日 -2 嗰晚 19:40 先出）' % tgt_date),
        'files': dwb[:3],
    })

    # ④ 21:00 Flow1 單日發票
    tgt_inv = 'inv_%s-%s-%s.xlsx' % (tgt.strftime('%d'), tgt.strftime('%m'), tgt.year)
    has_tgt = tgt_inv in invs
    steps.append({
        'id': 'w04', 'no': 4, 'name': '21:00 Flow1 · 單日發票', 'time': '21:00', 'auto': True,
        'script': 'gen_invoice_single.py',
        'artifact': 'inv_{DD}-{MM}-{YYYY}.xlsx',
        'path': 'OneDrive\\Desktop\\CDM\\CDM 發票對數\\CDM 發票\\{月文件夹}\\',
        'full': inv_full,
        'status': 'ok' if has_tgt else 'pending',
        'detail': '本月 %d 張（最新 %s）｜目標 %s：%s'
                  % (len(invs), invs_latest or '無', tgt_date,
                     '已出' if has_tgt else '未出'),
        'files': invs[-3:],
    })

    # ⑤ Flow1 三處同步
    f1s = get_flow1_sync()
    steps.append({
        'id': 'w05', 'no': 5, 'name': 'Flow1 · 三處同步', 'time': '21:00+', 'auto': True,
        'script': 'sync_shadow()（gen_invoice_single.py 內）',
        'artifact': '同一批 inv_* 落 2 份副本',
        'path': 'WorkBuddy\\Claw\\cdm\\ + WorkBuddy\\{工作區}\\cdm\\',
        'full': '%s ／ %s' % (CLAW_CDM, WS_CDM),
        'status': 'ok' if f1s.get('ok') else 'pending',
        'detail': '%s / %d 檔 / 缺 %d / 唔一致 %d（%s 檢查）'
                  % (f1s.get('folder'), f1s.get('files', 0),
                     len(f1s.get('missing', [])), len(f1s.get('mismatch', [])),
                     f1s.get('checked_at')),
        'files': [],
    })

    # ⑥ Flow2 5/6 日合併（人口令）
    flow2 = sorted(f for f in inv_files
                   if f.startswith('Inv_ ') and f.endswith('.xlsx'))
    steps.append({
        'id': 'w06', 'no': 6, 'name': 'Flow2 · 5/6 日合併發票', 'time': '人口令', 'auto': False,
        'script': 'gen_flow23_segment.py --month YYYY-MM --segment DD-DD',
        'artifact': 'Inv_ {DD}-{DD} MMM YYYY.xlsx',
        'path': 'OneDrive\\Desktop\\CDM\\CDM 發票對數\\CDM 發票\\{月文件夹}\\',
        'full': inv_full, 'status': 'ok' if flow2 else 'pending',
        'detail': '本月已有 %d 段：%s' % (len(flow2), '、'.join(flow2) if flow2 else '未做'),
        'files': flow2,
    })

    # ⑦ Flow3 金額對數（人口令）
    flow3 = sorted(f for f in inv_files
                   if f.startswith('CDM 金額對數') and f.endswith('.xlsx'))
    steps.append({
        'id': 'w07', 'no': 7, 'name': 'Flow3 · 金額對數', 'time': '人口令', 'auto': False,
        'script': 'gen_flow23_segment.py（同一腳本第二段）',
        'artifact': 'CDM 金額對數({DD}-{DD} MMM YYYY).xlsx',
        'path': 'OneDrive\\Desktop\\CDM\\CDM 發票對數\\CDM 發票\\{月文件夹}\\',
        'full': inv_full, 'status': 'ok' if flow3 else 'pending',
        'detail': '本月已有 %d 份：%s' % (len(flow3), '、'.join(flow3) if flow3 else '未做'),
        'files': flow3,
    })

    # ⑧ 打印 + email（人手）
    steps.append({
        'id': 'w08', 'no': 8, 'name': '打印 + email 出貨', 'time': '人手', 'auto': False,
        'script': '（人類：開 Flow2/3 檔 → 打印 → email）',
        'artifact': '打印機 TOSHIBA Universal Printer 2 ／ bensonkum86@gmail.com',
        'path': '打印紙本 + 收件箱存檔',
        'full': '', 'status': 'manual',
        'detail': 'Iron rule：Flow2/3 淨係 benso 手動撂口令，唔會自動跑',
        'files': [],
    })

    total = len(steps)
    done = sum(1 for s in steps if s['status'] == 'ok')
    pend = sum(1 for s in steps if s['status'] == 'pending')
    return {
        'target_date': tgt_date,
        'month_folder': name,
        'steps': steps,
        'total': total, 'done': done, 'pending': pend,
        'ok': done,
    }


def get_order_status():
    """檢查訂單狀態"""
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    
    order_folder = os.path.join(ONE_DRIVE_CDM, '訂單')
    pending_folder = os.path.join(ONE_DRIVE_CDM, 'pending_wechat')
    
    today_orders = []
    if os.path.exists(order_folder):
        today_orders = [f for f in os.listdir(order_folder) if today_str in f and f.endswith('.XLS')]
    
    pending_count = 0
    if os.path.exists(pending_folder):
        pending_count = len([f for f in os.listdir(pending_folder) if f.endswith('.json')])
    
    return {
        'today_count': len(today_orders),
        'today_files': today_orders[:3],  # 最多顯示 3 個
        'pending_count': pending_count
    }

def main():
    print('正在生成工作台狀態...')
    
    flow1_sync = get_flow1_sync()

    wf = get_cdm_workflow()

    status = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'inventory': get_inventory_data(),
        'cdm': get_cdm_status(),
        'orders': get_order_status(),
        'flow1_sync': flow1_sync,
        'cdm_workflow': wf,
        'last_backup': '2026-10-02'  # 從日誌讀取
    }

    # 寫入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f'✅ 狀態已生成: {OUTPUT_FILE}')
    print(f'   膠盒倉存: 小{status["inventory"]["small"]} / 大{status["inventory"]["big"]}')
    print(f'   CDM: {"正常" if status["cdm"]["ran_today"] else "未運行"}')
    print(f'   發票: {status["cdm"]["invoice_count"]} 張')
    print(f'   Flow1 三處同步: {"✅ 一致" if flow1_sync["ok"] else "❌ 有缺/唔一致"}'
          f'（{flow1_sync["folder"]} / {flow1_sync["files"]} 檔'
          f'／缺 {len(flow1_sync["missing"])}／唔一致 {len(flow1_sync["mismatch"])}）')
    print(f'   CDM 全流程跟進表: {wf["done"]}/{wf["total"]} 步完成'
          f'（{wf["pending"]} 待做；目標日 {wf["target_date"]}）')

    return status

if __name__ == '__main__':
    main()
