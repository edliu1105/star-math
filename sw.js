/* 星星回家 Service Worker
   策略：
     - 页面/脚本/manifest：网络优先 + 2.5s 超时 → 回落缓存（改 bug 后刷新一次就能拿到新版）
     - assets/*：缓存优先（离线可玩、加载快）
   缓存版本化，activate 时清理旧版本。 */
const VER   = "v6.9.0";
const SHELL = "shell-" + VER;
const MEDIA = "media-" + VER;
const NET_TIMEOUT = 2500;

const SHELL_URLS = ["./", "./index.html", "./manifest.webmanifest"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(SHELL)
      .then(c => c.addAll(SHELL_URLS).catch(() => c.add("./index.html").catch(() => {})))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.map(k => (k === SHELL || k === MEDIA) ? null : caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isMedia(url){
  return /\/assets\//.test(url.pathname) &&
         /\.(png|jpg|jpeg|webp|svg|woff2?|mp3|wav)$/i.test(url.pathname);
}

async function networkFirst(req){
  const cache = await caches.open(SHELL);
  try{
    const net = await new Promise((res, rej) => {
      const t = setTimeout(() => rej(new Error("timeout")), NET_TIMEOUT);
      fetch(req, { cache: "no-store" }).then(r => { clearTimeout(t); res(r); },
                                             e => { clearTimeout(t); rej(e); });
    });
    if(net && net.ok) cache.put(req, net.clone());
    return net;
  }catch(e){
    const hit = await cache.match(req) || await cache.match("./index.html");
    if(hit) return hit;
    throw e;
  }
}

async function cacheFirst(req){
  const cache = await caches.open(MEDIA);
  const hit = await cache.match(req);
  if(hit) return hit;
  const net = await fetch(req);
  if(net && net.ok) cache.put(req, net.clone());
  return net;
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if(req.method !== "GET") return;
  const url = new URL(req.url);
  if(url.origin !== self.location.origin) return;

  if(isMedia(url)){ e.respondWith(cacheFirst(req)); return; }

  if(req.mode === "navigate" ||
     /\.(html|webmanifest|json)$/i.test(url.pathname) ||
     url.pathname.endsWith("/")){
    e.respondWith(networkFirst(req));
    return;
  }
  // 其余（如 sw 自身之外的脚本）同样走网络优先，保证可更新
  e.respondWith(networkFirst(req));
});
