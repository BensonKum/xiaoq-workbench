# 工作台檢查清單

## 📋 狀態檢查步驟

### 1. 服務器檢查
- [ ] 本地服務器運行中 (端口 8082)
- [ ] HTTP 響應正常 (19,019 bytes)

### 2. 膠盒倉存數據
- [ ] Excel 文件存在: `C:\Users\benso\WorkBuddy\Claw\cdm\膠盒倉存(WB).xlsx`
- [ ] 最新數據: 小膠盒 **114,089** / 大膠盒 **45,151**
- [ ] 網頁顯示正確數值 ✅

### 3. CDM 流程狀態
- [ ] 最新記錄: `step_results_20260917.json`
- [ ] 今日 CDM 已執行: ✅
- [ ] PDF 已生成: ✅
- [ ] 微信發送: ✅

### 4. GitHub Pages 狀態
- [ ] `status.json` 可訪問: ✅
- [ ] CDM 狀態: ran_today = true
- [ ] Firestore 同步: 114 款產品

### 5. 訪問測試
- [ ] 本地訪問: `http://localhost:8082/tools-hub/index.html` ✅
- [ ] 手機訪問: `http://192.168.1.116:8082/tools-hub/index.html`

---

## ⚠️ 已知問題與解決方案

| 問題 | 原因 | 解決方案 |
|------|------|----------|
| 手機打唔開 | 防火牆阻止 LAN 連線 | 需要管理員權限添加防火牆規則 |
| Excel 數據過時 | 只有 4 月數據 | 使用用戶提供的 9 月數據 |
| API 服務器問題 | 路徑編碼問題 | 改用前端直接讀取 JSON |

---

## 🔧 快速修復命令

```bash
# 啟動服務器
python -m http.server 8082 --bind 0.0.0.0

# 檢查狀態
curl -s http://127.0.0.1:8082/tools-hub/index.html
```

---

## 📱 手機訪問（不同 WiFi）

如果手機唔喺同一個 WiFi，需要：
1. 部署到 GitHub Pages（免費公開訪問）
2. 或使用 ngrok 創建公開網址
