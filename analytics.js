(function () {
  'use strict';

  var MEASUREMENT_ID = 'G-MTD30PYWWH';
  var STORAGE_KEY = 'omicsHubCookieChoice';
  var loading = false;

  function hasAnalyticsConsent() {
    try { return window.localStorage.getItem(STORAGE_KEY) === 'accepted'; } catch (error) { return false; }
  }

  function loadAnalytics() {
    if (window.__omicsHubAnalyticsLoaded || loading || !hasAnalyticsConsent()) return;

    loading = true;
    if (typeof window.gtag === 'function') {
      window.gtag('consent', 'update', { analytics_storage: 'granted' });
    }

    var tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(MEASUREMENT_ID);
    tag.onload = function () {
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
      window.gtag('config', MEASUREMENT_ID, {
        anonymize_ip: true,
        send_page_view: true
      });
      window.__omicsHubAnalyticsLoaded = true;
      loading = false;
    };
    tag.onerror = function () { loading = false; };
    document.head.appendChild(tag);
  }

  window.omicsHubLoadAnalytics = loadAnalytics;
  loadAnalytics();
})();
