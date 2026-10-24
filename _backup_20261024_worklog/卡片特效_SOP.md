# 工作台 6 款卡片特效 ＋ 工作順序（順序排列）

> 全部程式喺 `Claw\tools-hub\index.html`（單一檔：`<style>` 段 + `<body>` DOM + `<script>` 段）。
> 版本現時 **v46**。收工一定要 publish，否則手機睇到嘅都係舊版。

---

## 一、6 款卡片特效（複製即用）

| # | 卡名 | class | 用喺邊 | 特效重點 | CSS 行 | 數據點 |
|---|---|---|---|---|---|---|
| ① | 自動化流程卡 | `.flow-card` | 工作流／流程頁（19:40 CDM、Flow1/2/3 等） | hover `scale(1.06)` + 深陰影；拖位排序；`.open` _hot_ 運動；`.linked` 圖示放大 1.12 | 81 / 145 / 151-154 | 手寫 DOM `data-id` + `FLOWS{}` 物件（step 文字） |
| ② | 指令／快捷卡 | `.cmd-card` | 一鍵指令（執行按鈕） | hover `scale(1.06)` + `brightness(1.07)`；`.cmd-btn` hover `scale(1.07)`；`:active` 還原 | 204 / 232 / 236-238 | 手寫 DOM + `onclick` |
| ③ | 祐興網站卡 | `.web-card` | 「祐興網站」新區（官網→倉存→訂單） | hover `translateY(-6px) scale(1.06)`；`.web-ico` 再上浮 3px；`:active` 回落 | 263 / 272 / 278-286 | **`WEB_SITES` 陣列自動生成**（改網址淨係改 `url` 欄） |
| ④ | 技能／口令卡 | `.skill-card` | 8 個 skill（cdm-workflow、super-tri-reporter…） | hover `translateY(-6px) scale(1.07)`；`:active` `scale(.97)` | 328 / 375-377 / 405-416 | 手寫 DOM |
| ⑤ | 篩選 chip | `.fb-chip` | 頂部篩選／刷新（refresh / cdm / inventory / reset） | hover `translateY(-2px)` + 主色邊；`:active` `scale(.98)`；`.active` 常態高亮 | 51 / 70-74 | `data-fb` 決定邊個 chip |
| ⑥ | 狀態提示三件套 | `.status-dot` `@keyframes pulse` / `.cmd-pop` / `.pwa-toast` | 在線圓點呼吸、底部指令彈窗、PWA 安裝提示 | `pulse` 2s 呼吸；`.show` 由 `opacity:0→1` + `translateY(24px→0)` | 95-96 / 295-299 / 453-460 | `pulse` 係純 CSS；`.show` 由 JS 加 class |

### ① flow-card（最常用，優先學識呢款）
```css
.flow-card, .cmd-card, .skill-card {
  transition: flex-basis .3s cubic-bezier(.2,0,.2,1), box-shadow .22s ease, transform .22s ease, border-color .25s ease;
}
.flow-card:hover { box-shadow: 0 12px 26px rgba(0,0,0,.6); border-color: #47566b; }
@media (hover: hover) and (pointer: fine) {
  .flow-card:not(.open):hover { transform: scale(1.06); z-index: 2; }
  .flow-card.open:hover { transform: none; }        /* 已展開就唔好再縮放 */
}
.run-card.dragging { z-index: 20; transition: none !important; cursor: grabbing; }
```
DOM：
```html
<div class="flow-card cdm" data-id="cdm" onclick="showFlow('cdm')"> … </div>
```
`data-id` 一定要同 `FLOWS{}` 嘅 key 一致，否則點開冇 step 文字。

### ③ web-card（改網址最易，推薦用）
```js
var WEB_SITES = [{ name:'祐興官網', url:'https://…', ico:'🏠' }, …];   // ← 唯一要改嘅位
WEB_SITES.forEach(function (site) { /* 自動生成 web-card */ });
```
```css
@media (hover: hover) and (pointer: fine) {
  .web-card:hover { transform: translateY(-6px) scale(1.06); z-index: 2; }
  .web-card:hover .web-ico { transform: translateY(-3px) scale(1.08); }
}
```

### ⑥ 狀態提示（呼吸點）
```css
.status-dot { background: var(--success); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .5; } }
```

---

## 二、工作順序（由零開始做一張新卡 —— 照呢個次序做，唔好跳）

### 1️⃣ 揀卡型（對照第一節 6 款）
流程 → ① flow-card；一鍵指令 → ② cmd-card；外鏈網站 → ③ web-card；skill/口令 → ④ skill-card；篩選/按鈕 → ⑤ fb-chip；提示 → ⑥ 三件套。
**唔好自己创新精神 new class** —— 沿用現有 6 款，改字改圖即可，改 class 會冇晒特效。

### 2️⃣ `<style>` 段加 CSS（行 ~40-470 之間）
- 一定寫 `transition`（transform + box-shadow + border-color），唔係就「即刻跳」好難睇。
- **hover 一定要包 `@media (hover: hover) and (pointer: fine)`** —— 唔包的手機點完會「黏住放大」。
- 加 `:active` 還原（`scale(.97)` / `translateY(-2px)`），摸落有回饋。
- 配色跟 v42 鐵規：卡片唔黑唔白，藍灰 `#22304d`。

### 3️⃣ `<body>` 段落 DOM
- flow-card / cmd-card / skill-card：**手寫** `<div class="…" data-id="…" onclick="showFlow('…')">`
- web-card：**唔使手寫**，改 `WEB_SITES` 就得（`.forEach` 自動建卡）
- chip：加 `.fb-chip` + `data-fb="refresh|cdm|inventory|reset"`

### 4️⃣ 接數據（三條通道，邊 type 用邊條）
| 數據 | 通道 | 注意 |
|---|---|---|
| 膠盒倉存 | `fetch('http://127.0.0.1:8083/api/inventory')` → 失敗就fallback `status.json` | 🚨 **唔好再用硬編碼舊數**（以前 114089/45151 就係咁錯） |
| 流程 step 文字 | `FLOWS{}` 物件（key = `data-id`） | 冇加就張卡點開係空白 |
| 網站網址 | `WEB_SITES[]` |  DataSource 單一，改一處就全別處跟 |

### 5️⃣ 本地預覽 + 截圖（出貨前必做）
```bash
curl -s --noproxy "*" http://127.0.0.1:8082/tools-hub/index.html | head -c 2000   # 系統代理會擋 localhost
```
截 desktop + mobile 兩張（`Claw\_v3_top.png` / `_v3_mobile.png` 就是咁嚟）。

### 6️⃣ publish（净係呢一條命令，跟住 deploy）
```bash
cd C:\Users\benso\WorkBuddy\Claw\tools-hub
python _publish.py          # 自動 +1 版本 → 寫 index.html + sw.js + APP_PUBLISHED → curl 對卡 → git commit
# 跟住 sites deploy（連結固定 https://xiaoq-workbench-76614.app.workbuddy.host/）
```
🚫 **唔用 `push_workbench.bat`**（根本唔存在；手動同步用 `_bump_sw.py`）。
publish 完：情人節藍色 ⟳ 檢查更新 vXX 位.Update → 手機 PWA 撳「⟳ 檢查更新 vXX」。

### 7️⃣ 收尾（好快但唔可以慳）
- `HANDOFF.md` §10.8–§10.12 publish checklist 打鈴勾。
- 新卡／新網址寫入 `MEMORY.md`（工作台版本 + 数据點）。
- Flow 卡若佢會拖位排序，記住 localStorage key `xq_flow_order_v1`。

---

## 三、五條鐵規（做卡記住）

1. ** Only v46 既配色**：#22304d 藍灰，卡片唔黑唔白（v42 鐵規）。
2. **hover 一定要包 `@media (hover: hover) and (pointer: fine)`**，否則手機黏住。
3. **publish 淨係 `python _publish.py` + sites deploy**；唔准喺第二部機 deploy（url 綁雲端 app ID → 線上會倒退 9/18 舊版、PWA 整冇）。
4. **倉存數字淨係一個源**：`api.py::read_box_latest()`（當月 sheet + 最後有日期行 + col6/col7），front_end 兩邊都讀佢。
5. **新卡唔好自己起 class**，用第 一節 6 款；要新 class 先講一聲。

---

## 四、一次做完嘅 check list

- [ ] 1️⃣ 揀好卡型（6 款其中一款）
- [ ] 2️⃣ `<style>` 加咗 transition + hover（包咗 media query）+ `:active`
- [ ] 3️⃣ DOM 落咗（web-card 就只改 `WEB_SITES`）
- [ ] 4️⃣ 數據接好（flow → `FLOWS{}`；倉存 → `api.py::read_box_latest`；網址 → `WEB_SITES`）
- [ ] 5️⃣ localhost 預覽 + desktop / mobile 截圖
- [ ] 6️⃣ `python _publish.py` → sites deploy → 線上對卡
- [ ] 7️⃣ 手機 PWA 撳「⟳ 檢查更新 vXX」睇到新卡
- [ ] 8️⃣ HANDOFF + MEMORY 記一筆
