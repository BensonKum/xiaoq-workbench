
// ===== 靜態配置（流程 + 技能 + 快捷鈕，動態嘢嚟自 status.json）=====
const WORKFLOWS = [
  {t:"錢大媽 CDM 自動化", slug:"cdm", code:["CDM"], s:"每晚 19:40/20:30/21:30 三輪。下載 Yahoo 訂單→執貨表→發票→PDF/打印→微信→email。target=today+2天。"},
  {t:"新增產品", slug:"new-product", code:["新產品","上新產品"], s:"讀工作指引→問名/價/分類→改 products_v2.json + inventory.html + Firestore doc + 借圖→sync+deploy+push。"},
  {t:"刪除 / 下架產品", slug:"del-product", code:["刪除產品","下架產品"], s:"問隱藏（推薦）定完全刪除，再執行對應方案。"},
  {t:"AB 卡（雙規格）", slug:"ab-card", code:["AB卡","雙規格卡"], s:"一卡兩 SKU，Tab 切換，SKU 尾 A 自動配對。"},
  {t:"Firestore /products 同步", slug:"sync-products", code:["sync products"], s:"跑 sync_products_to_firestore.py 推 107+ 款上雲。"},
  {t:"祐興報價單 Excel", slug:"quote", code:["報價單"], s:"gen_quote_xlsx.py 生成 103 款 + 相 + 分類分組。"},
  {t:"Beatra 廣告片", slug:"beatra", code:["廣告片"], s:"充值 ¥29 後 render 15 秒芝士番茄鮮肉餃（hero 相已收）。"},
  {t:"每日自動巡檢", slug:"patrol", code:["巡查"], s:"每晚 21:40 自動 report 去微信（CDM 跑咗未+出咗咩單）。"}
];

const SKILLS = [
  {n:"beatra-ai-video-studio", st:"active", note:"授權至~09-09，等充值¥29 render"},
  {n:"psd-poster-generator", st:"active", note:"13層分層PSD，餃子海報用過"},
  {n:"glm-image-generation（智譜）", st:"active", note:"API key 已配置，生成過概念圖"},
  {n:"find-skills", st:"active", note:"技能市場路由（專家廣場）"},
  {n:"qclaw-cron-skill", st:"active", note:"設 CDM 巡檢用"},
  {n:"agent-email / email-skill", st:"active", note:"郵件路由，CDM 發票靠佢"},
  {n:"tencent-docs", st:"idle", note:"寫入騰訊文檔用過"},
  {n:"libtv-cli", st:"down", note:"停用（收費貴 reject，skill 留底）"},
  {n:"build-xiaoq-workbench", st:"active", note:"自動搭建/部署小Q工作台（含技能狀態模板）"},
  {n:"yauhing-workflows", st:"active", note:"祐興/工作台 8 大流程 SOP"}
];

const QUICK = [
  {grp:"CDM", items:[
    {lab:"更新工作台", cmd:"更新工作台"},
    {lab:"重發發票 email", cmd:"重發發票 email"},
    {lab:"手動巡檢", cmd:"CDM 跑咗未"}
  ]},
  {grp:"祐興", items:[
    {lab:"sync products", cmd:"sync products"},
    {lab:"deploy 網站", cmd:"deploy 祐興網站"},
    {lab:"生成報價單", cmd:"生成祐興報價單"}
  ]},
  {grp:"備份", items:[
    {lab:"commit+push", cmd:"備份全部改動"}
  ]},
  {grp:"指定口令", items:[
    {lab:"新增產品", cmd:"新產品"},
    {lab:"下架產品", cmd:"下架產品"}
  ]}
];

const SITES = [
  {lab:"祐興食品網站", url:"https://yauhing-food.com/"},
  {lab:"倉存系統", url:"https://yauhing-food.com/inventory.html"},
  {lab:"取貨核實", url:"https://yauhing-food.com/verify.html"}
];

// ===== 渲染 =====
function renderStatic(){
  // 流程
  document.getElementById('workflows').innerHTML = WORKFLOWS.map(w=>`
    <div class="wf" data-slug="${w.slug}" style="cursor:pointer">
      <div class="t">${w.t} <span style="float:right;color:var(--cyan);font-size:.72rem">▶ 流程圖</span></div>
      <div>${(w.code||[]).map(c=>`<span class="code">${c}</span>`).join('')}</div>
      <div class="s">${w.s}</div>
    </div>`).join('');
  // 技能
  const sd = {active:['d-active','🟢'], down:['d-down','🔴'], idle:['d-idle','⚪']};
  document.getElementById('skills').innerHTML = SKILLS.map(s=>{
    const [cls]=sd[s.st];
    return `<div class="row"><div class="k"><span class="dot ${cls}"></span>${s.st==='active'?'活躍':s.st==='down'?'停用':'閒置'}</div><div class="v"><b>${s.n}</b><br><span style="color:var(--sub);font-size:.76rem">${s.note}</span></div></div>`;
  }).join('');
  // 快捷鈕
  let q = '';
  QUICK.forEach(g=>{
    q += `<div class="grp">${g.grp}</div><div class="btns">`+
      g.items.map((it,i)=>`<div class="btn" data-cmd="${it.cmd}"><span class="lab">${it.lab}</span><span class="cmd">${it.cmd}</span></div>`).join('')+
      `</div>`;
  });
  document.getElementById('quick').innerHTML = q;
  document.querySelectorAll('#workflows .wf').forEach(el=>{
    el.onclick=()=>{ location.href='workflows/'+el.dataset.slug+'.html'; };
  });
  document.querySelectorAll('.btn').forEach(b=>{
    b.onclick=()=>copyCmd(b.dataset.cmd);
  });
  // 網站快捷（開新頁跳轉）
  document.getElementById('sites').innerHTML = SITES.map(s2=>
    `<div class="btn" data-url="${s2.url}" style="cursor:pointer"><span class="lab">${s2.lab}</span><span class="cmd">${s2.url}</span></div>`).join('');
  document.querySelectorAll('#sites .btn').forEach(el=>{
    el.onclick=()=>{ window.open(el.dataset.url, '_blank'); };
  });
}

function copyCmd(cmd){
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(cmd).then(()=>toast('已複製：「'+cmd+'」 去微信搵小Q貼上')).catch(()=>toast('指令：'+cmd+'（請手動複製）'));
  } else {
    toast('指令：'+cmd);
  }
  // 嘗試跳 WeChat（唔一定成功，當 bonus）
  try{ window.location.href='weixin://'; }catch(e){}
}

function toast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove('show'),2600);
}

function badge(cls,txt){return `<span class="badge ${cls}">${txt}</span>`;}

function renderLive(d){
  if(!d){document.getElementById('live').innerHTML='<div class="loading">讀取失敗，可能未更新</div>';return;}
  const c=d.cdm||{};
  let h='';
  h+=`<div class="row"><div class="k">CDM 今晚</div><div class="v">${c.ran_today?badge('b-ok','已跑完'):badge('b-bad','未跑')} <span style="color:var(--sub)">target ${c.target_date||'?'}</span></div></div>`;
  h+=`<div class="row"><div class="k">PDF</div><div class="v">${c.pdf_ready?badge('b-ok','齊全'):badge('b-warn','缺')}</div></div>`;
  if(c.files&&c.files.length){
    c.files.forEach(f=>{h+=`<div class="row"><div class="k">📄</div><div class="v" style="font-size:.78rem">${f.name} <span style="color:var(--sub)">(${f.size_kb}KB)</span></div></div>`;});
  }
  const fs=d.firestore||{};
  h+=`<div class="row"><div class="k">Firestore</div><div class="v">/products 最後 sync：<b>${fs.products_synced_date||'?'}</b> <span style="color:var(--sub)">(${fs.products_count||'?'} docs)</span></div></div>`;
  const td=(d.todos||[]).filter(t=>!t.done).length;
  h+=`<div class="row"><div class="k">待辦</div><div class="v">${td} 項未完成</div></div>`;
  document.getElementById('live').innerHTML=h;
  document.getElementById('updated').textContent='最後更新：'+(d.generated_at||'?');
}

function renderTodos(d){
  if(!d||!d.todos){document.getElementById('todos').innerHTML='<div class="loading">讀取失敗</div>';return;}
  document.getElementById('todos').innerHTML=d.todos.map(t=>`
    <div class="todo ${t.done?'done':''}"><div class="box">${t.done?'✓':''}</div><div class="tx">${t.text}</div></div>`).join('');
}

// ===== 載入 =====
renderStatic();
fetch('status.json?t='+Date.now(),{cache:'no-store'})
  .then(r=>r.ok?r.json():null)
  .then(d=>{ if(d){renderLive(d);renderTodos(d);} else {renderLive(null);} })
  .catch(()=>renderLive(null));
