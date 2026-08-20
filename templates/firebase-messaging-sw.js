/*
 * firebase-messaging-sw.js
 * -------------------------
 * Firebase Cloud Messaging service worker. Must live at the SITE ROOT
 * (not under /articles/, not under templates/ once built) because a
 * service worker's scope is limited to the directory it's served from
 * and everything below it -- root is what lets it cover the whole site.
 *
 * This is the "compat" SDK loaded via importScripts because service
 * workers on a no-build static site can't easily use ES module imports
 * from a CDN. Matches the compat scripts loaded in base.html.
 *
 * Config note: a service worker runs in its own execution context, so it
 * can't read `window.firebaseConfig` off the page. Instead subscribe.js
 * registers this worker with the config passed as a URL query string
 * (?firebaseConfig=<url-encoded JSON>), and we parse it back out below.
 * This keeps the Firebase config in exactly ONE place in the source
 * (base.html) instead of duplicated across two files.
 */
importScripts("https://www.gstatic.com/firebasejs/10.13.2/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.13.2/firebase-messaging-compat.js");

var params = new URL(self.location.href).searchParams;
var configParam = params.get("firebaseConfig");

if (configParam) {
  var firebaseConfig = JSON.parse(decodeURIComponent(configParam));
  firebase.initializeApp(firebaseConfig);

  var messaging = firebase.messaging();

  // Background handler -- fires when a push arrives while no CardPulse tab
  // is focused. Foreground pushes (tab open) are handled in subscribe.js
  // instead, since this handler never fires for those.
  messaging.onBackgroundMessage(function (payload) {
    var title = (payload.notification && payload.notification.title) || "CardPulse";
    var body = (payload.notification && payload.notification.body) || "A card you follow just moved.";
    var options = {
      body: body,
      icon: (payload.notification && payload.notification.icon) || "/icon-192.png",
      badge: "/icon-192.png",
      data: { url: (payload.data && payload.data.url) || "/" }
    };
    self.registration.showNotification(title, options);
  });
}

// Clicking a notification focuses an existing CardPulse tab if one is
// open, otherwise opens the target URL in a new one.
self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  var targetUrl = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (windowClients) {
      for (var i = 0; i < windowClients.length; i++) {
        var client = windowClients[i];
        if (client.url.indexOf(self.location.origin) === 0 && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
