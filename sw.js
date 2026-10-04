/* 祐興工作台 Service Worker —— 離線快取 + 令 PWA 可安裝
 * 版本號必須同 index.html 嘅 APP_VERSION 一致（用 _bump_sw.py 自動同步）
 */
const APP_VER = 'v50';
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
  );
});
