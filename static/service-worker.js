const CACHE = "conect-pwa-v2";
const ARQUIVOS = [
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/css/style.css",
  "/static/manifest.webmanifest"
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ARQUIVOS)));
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((chave) => chave !== CACHE).map((chave) => caches.delete(chave)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  if (evento.request.method !== "GET") return;
  const url = new URL(evento.request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname === "/static/css/style.css") {
    // CSS sempre tenta a rede primeiro. Evita a tela sem estilo/estilo antigo após atualização.
    evento.respondWith(
      fetch(evento.request).then((rede) => {
        const copia = rede.clone();
        caches.open(CACHE).then((cache) => cache.put(evento.request, copia));
        return rede;
      }).catch(() => caches.match(evento.request))
    );
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    evento.respondWith(
      caches.match(evento.request).then((resposta) =>
        resposta || fetch(evento.request).then((rede) => {
          const copia = rede.clone();
          caches.open(CACHE).then((cache) => cache.put(evento.request, copia));
          return rede;
        })
      )
    );
  }
});
