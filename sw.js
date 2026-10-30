/* 祐興工作台 Service Worker —— 離線快取 + 令 PWA 可安裝
 * 版本號必須同 index.html 嘅 APP_VERSION 一致（用 _bump_sw.py 自動同步）
 */
const APP_VER = 'v86';
const CACHE = 'xq-workbench-' + APP_VER;
const ASSETS = [
  './', './index.html', './manifest.json',
  './icon-192.png', './icon-512.png', './apple-touch-icon.png', './favicon-32.png'
];

/* 主頁（navigation）用網絡優先：一開 PWA 就見到最新版本；斷網才跌回快取 */
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  /* sw.js 自己：永遠網絡優先、唔入快取。否則舊 SW 會快取自己，
     令瀏覽器嘅 SW update 檢查永遠攞唔到新版（手機卡死主因）。 */
  if (url.pathname.endsWith('/sw.js')) {
    e.respondWith(fetch(req));
    return;
  }

  if (req.mode === 'navigate' || (req.headers.get('accept') || '').indexOf('text/html') > -1) {
    e.respondWith(
      fetch(req).then((res) => {
        if (res && res.status === 200 && res.type === 'basic') {
          try { caches.open(CACHE).then((c) => c.put('./index.html', res.clone())); } catch (_) {}
        }
        return res;
      }).catch(() =>
        caches.open(CACHE).then((c) => c.match(req).then((h) => h || c.match('./index.html')))
      )
    );
    return;
  }

  /* 其他資源：快取優先（離線都開到）+ 背景補快取 */
  e.respondWith(
    caches.open(CACHE).then((c) =>
      c.match(req).then((hit) => {
        if (hit) return hit;
        return fetch(req).then((res) => {
          if (res && res.status === 200 && res.type === 'basic') {
            try { c.put(req, res.clone()); } catch (_) {}
          }
          return res;
        });
      })
    )
  );
});

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(ASSETS.map((a) => c.add(a).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

/* 檯面撳「更新」→ 叫新版 SW 立刻接手 */
self.addEventListener('message', (e) => {
  if (e.data && (e.data.type === 'SKIP_WAITING' || e.data.type === 'sync')) self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
      .then(() => {
        /* 根治「舊 SW 鎖死緩存、頁面卡住唔更新」：新版 SW 一接手，
           強制所有已開頁面重新導航去最新版（network-first 會攞到新頁）。
           只喺版本變更時 activate 一次，唔會無限 loop。 */
        return self.clients.matchAll({ includeUncontrolled: true, type: 'window' })
          .then((cs) => cs.forEach((c) => { try { c.navigate(c.url); } catch (_) {} }));
      })
  );
});
