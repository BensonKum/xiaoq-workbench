/* 祐興工作台 Service Worker —— 離線快取 + 令 PWA 可安裝 */
const CACHE = 'xq-workbench-v35';
const ASSETS = [
  './', './index.html', './manifest.json',
  './icon-192.png', './icon-512.png', './apple-touch-icon.png', './favicon-32.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS).catch(() => {})).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  e.respondWith(
    caches.open(CACHE).then((c) =>
      c.match(req).then((hit) => {
        if (hit) return hit;                       // 快取優先（離線都開到）
        return fetch(req).then((res) => {
          if (res && res.status === 200 && res.type === 'basic') {
            try { c.put(req, res.clone()); } catch (_) {}
          }
          return res;
        }).catch(() => c.match('./index.html').then(h => h || Response.error()));
      })
    )
  );
});
