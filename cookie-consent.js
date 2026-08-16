(function () {
  'use strict';

  var STORAGE_KEY = 'omicsHubCookieChoice';
  var banner = document.getElementById('cookie-consent-banner');
  var panel = document.getElementById('cookie-preferences-panel');
  var status = document.getElementById('cookie-preferences-status');

  function getChoice() {
    try { return window.localStorage.getItem(STORAGE_KEY); } catch (error) { return null; }
  }

  window.omicsHubUpdateConsent = function (choice) {
    if (typeof window.gtag !== 'function') return;
    var granted = choice === 'accepted' ? 'granted' : 'denied';
    window.gtag('consent', 'update', { ad_storage: granted, analytics_storage: granted, ad_user_data: granted, ad_personalization: granted });
  };

  function saveChoice(choice) {
    try { window.localStorage.setItem(STORAGE_KEY, choice); } catch (error) { /* Continue without persistence. */ }
    document.documentElement.dataset.cookieChoice = choice;
    if (typeof window.omicsHubUpdateConsent === 'function') window.omicsHubUpdateConsent(choice);
  }

  function hideBanner() {
    if (banner) banner.classList.add('hidden');
  }

  function openPreferences() {
    if (!panel) return;
    panel.classList.remove('hidden');
    panel.setAttribute('aria-hidden', 'false');
    if (status) status.textContent = 'Choose whether optional cookies may be used on this device.';
  }

  function closePreferences() {
    if (!panel) return;
    panel.classList.add('hidden');
    panel.setAttribute('aria-hidden', 'true');
  }

  function applyChoice(choice) {
    saveChoice(choice);
    hideBanner();
    closePreferences();
    if (status) status.textContent = choice === 'accepted' ? 'Optional cookies accepted.' : 'Optional cookies declined.';
  }

  document.querySelectorAll('[data-cookie-choice]').forEach(function (button) {
    button.addEventListener('click', function () { applyChoice(button.getAttribute('data-cookie-choice')); });
  });
  document.querySelectorAll('[data-cookie-preferences]').forEach(function (button) {
    button.addEventListener('click', openPreferences);
  });
  document.querySelectorAll('[data-cookie-close]').forEach(function (button) {
    button.addEventListener('click', closePreferences);
  });

  if (getChoice()) hideBanner();
})();
