(function () {
  'use strict';

  var STORAGE_KEY = 'omicsHubCookieChoice';
  var banner = document.getElementById('cookie-consent-banner');
  var policyLink = banner && banner.querySelector('a[href]');
  var policyHref = policyLink ? policyLink.getAttribute('href') : '/pages/cookie.html';
  var previousFocus = null;

  function getChoice() {
    try { return window.localStorage.getItem(STORAGE_KEY); } catch (error) { return null; }
  }

  // This control covers analytics only. It is not a Google-certified advertising CMP.
  // Advertising consent must be collected separately by a configured certified CMP.
  window.omicsHubUpdateConsent = function (choice) {
    if (typeof window.gtag !== 'function') return;
    window.gtag('consent', 'update', {
      analytics_storage: choice === 'accepted' ? 'granted' : 'denied'
    });
  };

  function clearAnalyticsCookies() {
    document.cookie.split(';').forEach(function (entry) {
      var name = entry.split('=')[0].trim();
      if (!/^(_ga(?:_|$)|_gid$|_gat(?:_|$))/.test(name)) return;
      var domains = [null, window.location.hostname, '.' + window.location.hostname];
      var parts = window.location.hostname.split('.');
      if (parts.length > 2) domains.push('.' + parts.slice(1).join('.'));
      domains.forEach(function (domain) {
        document.cookie = name + '=; Max-Age=0; path=/' + (domain ? '; domain=' + domain : '') + '; SameSite=Lax';
      });
    });
  }

  function saveChoice(choice) {
    try { window.localStorage.setItem(STORAGE_KEY, choice); } catch (error) { /* Continue without persistence. */ }
    document.documentElement.dataset.cookieChoice = choice;
    window.omicsHubUpdateConsent(choice);
    if (choice === 'accepted' && typeof window.omicsHubLoadAnalytics === 'function') window.omicsHubLoadAnalytics();
    if (choice === 'declined') clearAnalyticsCookies();
  }

  var panel = document.getElementById('cookie-preferences-panel');
  if (!panel) {
    panel = document.createElement('dialog');
    panel.id = 'cookie-preferences-panel';
    panel.className = 'cookie-preferences-dialog';
    panel.setAttribute('aria-labelledby', 'cookie-preferences-heading');
    panel.innerHTML = '<h2 id="cookie-preferences-heading">Cookie Preferences</h2>' +
      '<p>Choose whether to allow Google Analytics to measure how this site is used. Browsing does not require analytics cookies. Your preference is stored in this browser.</p>' +
      '<p>This control does not provide consent for personalized advertising. Any advertising consent must be managed separately through the applicable consent-management service.</p>' +
      '<p id="cookie-preferences-status" role="status"></p>' +
      '<p><a id="cookie-preferences-policy">Read the Cookie Policy</a></p>' +
      '<div class="cookie-preferences-actions">' +
      '<button type="button" data-cookie-choice="declined">Decline analytics</button>' +
      '<button type="button" data-cookie-choice="accepted">Allow analytics</button>' +
      '<button type="button" data-cookie-close>Close</button></div>';
    panel.querySelector('#cookie-preferences-policy').setAttribute('href', policyHref);
    document.body.appendChild(panel);
  }
  var status = panel.querySelector('#cookie-preferences-status');

  if (!document.querySelector('[data-cookie-preferences]')) {
    var trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'cookie-preferences-link';
    trigger.setAttribute('data-cookie-preferences', '');
    trigger.setAttribute('aria-haspopup', 'dialog');
    trigger.setAttribute('aria-controls', panel.id);
    trigger.textContent = 'Cookie Preferences';
    var footer = document.querySelector('footer');
    var footerPolicy = footer && footer.querySelector('a[href*="cookie.html"]');
    if (footerPolicy && footerPolicy.closest('li')) {
      var item = document.createElement('li');
      item.appendChild(trigger);
      footerPolicy.closest('li').parentElement.appendChild(item);
    } else {
      (footer || document.body).appendChild(trigger);
    }
  }

  if (banner) {
    var paragraphs = banner.querySelectorAll('p');
    if (paragraphs[0]) paragraphs[0].textContent = 'Analytics preferences';
    if (paragraphs[1] && policyLink) {
      paragraphs[1].textContent = 'Allow optional Google Analytics cookies to help improve the site, or decline them. Your choice is stored in this browser. See our ';
      paragraphs[1].appendChild(policyLink);
      paragraphs[1].appendChild(document.createTextNode(' for details.'));
    }
    banner.querySelectorAll('[data-cookie-choice]').forEach(function (button) {
      button.textContent = button.getAttribute('data-cookie-choice') === 'accepted' ? 'Allow analytics' : 'Decline analytics';
      button.type = 'button';
    });
  }

  function closePreferences() {
    if (panel.open) panel.close();
    if (previousFocus && previousFocus.isConnected) previousFocus.focus();
  }

  function openPreferences() {
    previousFocus = document.activeElement;
    if (status) status.textContent = getChoice() === 'accepted' ? 'Analytics is currently allowed.' : 'Analytics is currently declined or has not been allowed.';
    if (!panel.open) panel.showModal();
  }

  function applyChoice(choice) {
    if (choice !== 'accepted' && choice !== 'declined') return;
    var reloadRequired = choice === 'declined' && Boolean(window.__omicsHubAnalyticsLoaded);
    saveChoice(choice);
    if (banner) banner.classList.add('hidden');
    closePreferences();
    if (status) status.textContent = choice === 'accepted' ? 'Analytics allowed.' : 'Analytics declined.';
    // Reload after withdrawing consent so the already-loaded analytics library stops running.
    if (reloadRequired) window.location.reload();
  }

  document.addEventListener('click', function (event) {
    var choiceButton = event.target.closest('button[data-cookie-choice]');
    if (choiceButton) applyChoice(choiceButton.getAttribute('data-cookie-choice'));
    else if (event.target.closest('[data-cookie-preferences]')) openPreferences();
    else if (event.target.closest('[data-cookie-close]')) closePreferences();
  });
  panel.addEventListener('cancel', function () {
    if (previousFocus && previousFocus.isConnected) previousFocus.focus();
  });

  var existingChoice = getChoice();
  if (existingChoice === 'accepted' || existingChoice === 'declined') {
    saveChoice(existingChoice);
    if (banner) banner.classList.add('hidden');
  }
})();
