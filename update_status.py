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
    
    status = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'inventory': get_inventory_data(),
        'cdm': get_cdm_status(),
        'orders': get_order_status(),
        'last_backup': '2026-10-02'  # 從日誌讀取
    }
    
    # 寫入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    
    print(f'✅ 狀態已生成: {OUTPUT_FILE}')
    print(f'   膠盒倉存: 小{status["inventory"]["small"]} / 大{status["inventory"]["big"]}')
    print(f'   CDM: {"正常" if status["cdm"]["ran_today"] else "未運行"}')
    print(f'   發票: {status["cdm"]["invoice_count"]} 張')
    
    return status

if __name__ == '__main__':
    main()
