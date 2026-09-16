#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
祐興工作台 API 後端
提供數據讀取和狀態檢查功能
"""
import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import openpyxl

# 文件路徑
INVENTORY_FILE = r'C:\Users\benso\WorkBuddy\Claw\cdm\膠盒倉存(WB).xlsx'
CDM_DIR = r'C:\Users\benso\WorkBuddy\Claw\cdm'

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
        """讀取膠盒倉存數據"""
        try:
            wb = openpyxl.load_workbook(INVENTORY_FILE)
            ws = wb.active
            
            # 讀取最後一行數據
            last_row = ws.max_row
            small_box = ws.cell(last_row, 4).value  # 產品1-10 結餘
            big_box = ws.cell(last_row, 5).value   # 產品11-12 結餘
            
            # 讀取最後日期
            last_date = ws.cell(last_row - 2, 1).value
            
            data = {
                'success': True,
                'small_box': small_box or 0,
                'big_box': big_box or 0,
                'last_update': str(last_date) if last_date else '未知',
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
            wb = openpyxl.load_workbook(INVENTORY_FILE)
            ws = wb.active
            last_row = ws.max_row
            result['inventory'] = {
                'small_box': ws.cell(last_row, 4).value,
                'big_box': ws.cell(last_row, 5).value,
                'last_date': str(ws.cell(last_row - 2, 1).value)
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
