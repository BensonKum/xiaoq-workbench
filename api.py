#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
祐興工作台 API 後端
提供數據讀取和狀態檢查功能
"""
import os
import json
import re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import openpyxl

# 文件路徑
INVENTORY_FILE = r'C:\Users\benso\WorkBuddy\Claw\cdm\膠盒倉存(WB).xlsx'
CDM_DIR = r'C:\Users\benso\WorkBuddy\Claw\cdm'

# 🚨 2026-10-03 修：倉存頁結餘一定要用「當月 sheet + 最新有日期嗰行 + col6/col7」
#    - 舊 code 用 wb.active（openpyxl 開出嚟第一頁 = 「4月」）→ 回 4 月嘅數字
#    - 舊 code 又用 col4/col5（標準頁 D/E 係「補貨」欄，唔係結餘）→ 出 '-'
# 標準頁欄位：A日期 B/C用量 D/E補貨 F/G結餘 H總用量
DATE_RE = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}')


def read_box_latest(path=INVENTORY_FILE):
    """回 {'small':int,'big':int,'date':str} —— 當月 sheet 最新有日期嗰行嘅結餘"""
    wb = openpyxl.load_workbook(path, data_only=True)
    try:
        today = datetime.now()
        sheet = None
        for name in wb.sheetnames:                      # 1) 揀當月 sheet
            if str(name) == '%d月' % today.month:
                sheet = wb[name]
                break
        if sheet is None:                                # 2) 冇就 fallback 翻最新嘅月份頁
            sheet = wb[wb.sheetnames[-1]]

        last = None                                      # 3) 搵最後一個「有日期」嘅行
        for r in range(sheet.max_row, 0, -1):
            v = sheet.cell(r, 1).value
            if v is None:
                continue
            if DATE_RE.match(str(v).strip()):
                last = r
                break
        if last is None:
            return {'small': 0, 'big': 0, 'date': '未知'}

        small = sheet.cell(last, 6).value or 0           # F = 小膠盒結餘
        big = sheet.cell(last, 7).value or 0             # G = 大膠盒結餘
        date = sheet.cell(last, 1).value
        return {'small': small, 'big': big,
                'date': str(date)[:10] if date else '未知'}
    finally:
        wb.close()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/inventory':
            self.send_inventory()
        elif self.path == '/api/cdm-status':
            self.send_cdm_status()
        elif self.path == '/api/check-all':
            self.send_all_check()
        else:
            self.send_error(404, 'Not found')
    
    def send_inventory(self):
        """讀取膠盒倉存數據（當月 sheet 最新日嘅結餘）"""
        try:
            box = read_box_latest()
            data = {
                'success': True,
                'small_box': box['small'],
                'big_box': box['big'],
                'last_update': box['date'],
                'file_path': INVENTORY_FILE
            }
            self.send_json(data)
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)})
    
    def send_cdm_status(self):
        """檢查 CDM 流程狀態"""
        try:
            # 檢查 CDM 輸出路徑
            output_dir = os.path.join(CDM_DIR, '輸出')
            pdf_files = []
            if os.path.exists(output_dir):
                pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
            
            # 檢查最新的訂單處理記錄
            processed_files = []
            for f in os.listdir(CDM_DIR):
                if f.startswith('processed_') and f.endswith('.json'):
                    processed_files.append(f)
            
            data = {
                'success': True,
                'cdm_running': len(pdf_files) > 0,
                'latest_pdf_count': len(pdf_files),
                'processed_orders': len(processed_files),
                'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.send_json(data)
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)})
    
    def send_all_check(self):
        """執行全盤檢查"""
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'inventory': None,
            'cdm': None
        }
        
        # 檢查膠盒倉存
        try:
            box = read_box_latest()
            result['inventory'] = {
                'small_box': box['small'],
                'big_box': box['big'],
                'last_date': box['date']
            }
        except Exception as e:
            result['inventory_error'] = str(e)
        
        # 檢查 CDM
        try:
            output_dir = os.path.join(CDM_DIR, '輸出')
            pdf_files = []
            if os.path.exists(output_dir):
                pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
            result['cdm'] = {
                'running': len(pdf_files) > 0,
                'pdf_count': len(pdf_files)
            }
        except Exception as e:
            result['cdm_error'] = str(e)
        
        self.send_json(result)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': False, 'error': message}).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # 靜默日誌

if __name__ == '__main__':
    port = 8083
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'API server running on port {port}')
    server.serve_forever()
