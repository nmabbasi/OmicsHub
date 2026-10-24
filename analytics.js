(function () {
  'use strict';

  var MEASUREMENT_ID = 'G-MTD30PYWWH';
  var STORAGE_KEY = 'omicsHubCookieChoice';
  var loading = false;
  var waitingForDefaults = false;
  var scriptReady = false;

  function hasAnalyticsConsent() {
    try { return window.localStorage.getItem(STORAGE_KEY) === 'accepted'; } catch (error) { return false; }
  }

  function hasConsentDefaultsAndQueue() {
    if (!Array.isArray(window.dataLayer) || typeof window.gtag !== 'function') return false;

    for (var i = 0; i < window.dataLayer.length; i += 1) {
      var command = window.dataLayer[i];
      var defaults = command && command[0] === 'consent' && command[1] === 'default' && command[2];
      if (defaults && defaults.analytics_storage === 'denied' &&
          defaults['ad_storage'] === 'denied' && defaults['ad_user_data'] === 'denied' &&
          defaults['ad_personalization'] === 'denied') return true;
    }
    return false;
  }

  function loadAnalytics() {
    if (window.__omicsHubAnalyticsLoaded || loading || !hasAnalyticsConsent()) return;

    // Synchronous analytics.js tags can run before the following inline defaults.
    // Wait for parsing to finish; if defaults are missing or malformed, fail closed.
    if (document.readyState === 'loading') {
      if (!waitingForDefaults) {
        waitingForDefaults = true;
        document.addEventListener('DOMContentLoaded', function () {
          waitingForDefaults = false;
          loadAnalytics();
        }, { once: true });
      }
      return;
    }
    if (!hasConsentDefaultsAndQueue()) return;

    loading = true;
    window.gtag('consent', 'update', { analytics_storage: 'granted' });

    if (scriptReady) {
      configureAnalytics();
      loading = false;
      return;
    }

    var tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(MEASUREMENT_ID);
    tag.onload = function () {
      scriptReady = true;
      // Consent may have been withdrawn while the external script was downloading.
      if (!hasAnalyticsConsent()) {
        loading = false;
        return;
      }
      configureAnalytics();
      loading = false;
    };
    tag.onerror = function () { loading = false; };
    document.head.appendChild(tag);
  }

  function configureAnalytics() {
    window.gtag('js', new Date());
    window.gtag('config', MEASUREMENT_ID, {
      anonymize_ip: true,
      send_page_view: true
    });
    window.__omicsHubAnalyticsLoaded = true;
  }

  window.omicsHubLoadAnalytics = loadAnalytics;
  loadAnalytics();
})();
