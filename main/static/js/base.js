/**
 * Errors2Experts — Base JavaScript
 * File: main/static/js/base.js
 *
 * Shared behaviour only:
 * - AOS initialization
 * - Fixed navbar state and mobile-menu closing
 * - Django-message dismissal
 * - Offer/career modal
 * - Global toast API
 * - Demo booking AJAX hook
 * - Same-page smooth scrolling
 * - Internal page transition
 *
 * Page-specific behaviour belongs in page-specific JavaScript files.
 */

(() => {
  'use strict';

  const SELECTORS = Object.freeze({
    body: 'body.e2e-base-page',
    navbar: '#mainNavbar',
    navbarCollapse: '#mainNavigation',
    navCloseLinks:
      '#mainNavigation a.nav-link:not(.dropdown-toggle), #mainNavigation .dropdown-item',
    djangoAlerts: '.site-alert',
    offerModal: '#e2eOfferModal',
    offerTriggers: '[data-offer-trigger]',
    demoForm: '#demoForm',
    mainContent: '#main-content',
  });

  const CLASSES = Object.freeze({
    navbarScrolled: 'e2e-base-navbar--scrolled',
    pageLeaving: 'e2e-base-page--leaving',
    toastRegion: 'e2e-base-toast-region',
    toast: 'e2e-base-toast',
    toastLeaving: 'e2e-base-toast--leaving',
    submitLoading: 'e2e-base-submit-loading',
  });

  const SETTINGS = Object.freeze({
    navbarScrollPoint: 48,
    offerDelay: 1400,
    messageDuration: 6500,
    toastDuration: 4200,
    pageTransitionDuration: 160,
  });

  const ready = (callback) => {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback, { once: true });
      return;
    }

    callback();
  };

  const query = (selector, parent = document) => parent.querySelector(selector);

  const queryAll = (selector, parent = document) => [
    ...parent.querySelectorAll(selector),
  ];

  const prefersReducedMotion = () =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const getBody = () => query(SELECTORS.body);

  /* ------------------------------------------------------------------------
     Toasts
     ------------------------------------------------------------------------ */

  const getToastIcon = (type) => {
    const icons = {
      success: 'bi-check-circle-fill',
      error: 'bi-exclamation-circle-fill',
      warning: 'bi-exclamation-triangle-fill',
      info: 'bi-info-circle-fill',
    };

    return icons[type] || icons.info;
  };

  const getToastRegion = () => {
    let region = query(`.${CLASSES.toastRegion}`);

    if (region) {
      return region;
    }

    region = document.createElement('div');
    region.className = CLASSES.toastRegion;
    region.setAttribute('aria-live', 'polite');
    region.setAttribute('aria-atomic', 'false');
    document.body.appendChild(region);

    return region;
  };

  const removeToast = (toast) => {
    if (!toast || toast.dataset.removing === 'true') {
      return;
    }

    toast.dataset.removing = 'true';
    toast.classList.add(CLASSES.toastLeaving);

    window.setTimeout(() => {
      toast.remove();

      const region = query(`.${CLASSES.toastRegion}`);
      if (region && !region.children.length) {
        region.remove();
      }
    }, 190);
  };

  const showToast = (
    message,
    type = 'info',
    duration = SETTINGS.toastDuration,
  ) => {
    const cleanMessage = String(message || '').trim();

    if (!cleanMessage) {
      return null;
    }

    const allowedTypes = new Set(['success', 'error', 'warning', 'info']);
    const safeType = allowedTypes.has(type) ? type : 'info';

    // Success submissions use the larger E2E animated feedback.
    // Errors/warnings/info remain compact toasts.
    if (
      safeType === 'success' &&
      window.E2EFeedback &&
      typeof window.E2EFeedback.show === 'function'
    ) {
      window.E2EFeedback.show({
        message: cleanMessage,
        type: 'success',
        kind: 'auto',
        duration:
          Number.isFinite(duration) && duration > 0
            ? Math.max(duration, 5000)
            : 5600,
      });

      return null;
    }

    const region = getToastRegion();
    const toast = document.createElement('div');

    toast.className = `${CLASSES.toast} ${CLASSES.toast}--${safeType}`;
    toast.setAttribute('role', safeType === 'error' ? 'alert' : 'status');

    const icon = document.createElement('span');
    icon.className = `${CLASSES.toast}__icon`;
    icon.setAttribute('aria-hidden', 'true');
    icon.innerHTML = `<i class="bi ${getToastIcon(safeType)}"></i>`;

    const text = document.createElement('span');
    text.className = `${CLASSES.toast}__message`;
    text.textContent = cleanMessage;

    const closeButton = document.createElement('button');
    closeButton.className = `${CLASSES.toast}__close`;
    closeButton.type = 'button';
    closeButton.setAttribute('aria-label', 'Close notification');
    closeButton.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';
    closeButton.addEventListener('click', () => removeToast(toast));

    toast.append(icon, text, closeButton);
    region.appendChild(toast);

    if (Number.isFinite(duration) && duration > 0) {
      window.setTimeout(() => removeToast(toast), duration);
    }

    return toast;
  };

  /* ------------------------------------------------------------------------
     AOS
     ------------------------------------------------------------------------ */

  const initAos = () => {
    if (!window.AOS) {
      return;
    }

    if (prefersReducedMotion()) {
      queryAll('[data-aos]').forEach((element) => {
        element.removeAttribute('data-aos');
        element.removeAttribute('data-aos-delay');
        element.removeAttribute('data-aos-duration');
      });
      return;
    }

    window.AOS.init({
      duration: 720,
      easing: 'ease-out-cubic',
      once: false,
      mirror: false,
      offset: 55,
      anchorPlacement: 'top-bottom',
    });
  };

  /* ------------------------------------------------------------------------
     Navbar
     ------------------------------------------------------------------------ */

  const initNavbar = () => {
    const navbar = query(SELECTORS.navbar);

    if (!navbar) {
      return;
    }

    let ticking = false;

    const updateNavbar = () => {
      navbar.classList.toggle(
        CLASSES.navbarScrolled,
        window.scrollY > SETTINGS.navbarScrollPoint,
      );
      ticking = false;
    };

    const requestNavbarUpdate = () => {
      if (ticking) {
        return;
      }

      ticking = true;
      window.requestAnimationFrame(updateNavbar);
    };

    window.addEventListener('scroll', requestNavbarUpdate, { passive: true });
    updateNavbar();

    const collapseElement = query(SELECTORS.navbarCollapse);

    if (!collapseElement || !window.bootstrap) {
      return;
    }

    queryAll(SELECTORS.navCloseLinks, collapseElement).forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth >= 992) {
          return;
        }

        const collapse =
          window.bootstrap.Collapse.getInstance(collapseElement) ||
          window.bootstrap.Collapse.getOrCreateInstance(collapseElement, {
            toggle: false,
          });

        collapse.hide();
      });
    });
  };

  /* ------------------------------------------------------------------------
     Django messages
     ------------------------------------------------------------------------ */

  const initDjangoMessages = () => {
    if (!window.bootstrap) {
      return;
    }

    queryAll(SELECTORS.djangoAlerts).forEach((alertElement, index) => {
      const alert = window.bootstrap.Alert.getOrCreateInstance(alertElement);
      const delay = SETTINGS.messageDuration + index * 350;

      window.setTimeout(() => {
        if (document.body.contains(alertElement)) {
          alert.close();
        }
      }, delay);
    });
  };

  /* ------------------------------------------------------------------------
     Offer or career modal
     ------------------------------------------------------------------------ */

  const safelyReadSession = (key) => {
    try {
      return window.sessionStorage.getItem(key);
    } catch (error) {
      return null;
    }
  };

  const safelyWriteSession = (key, value) => {
    try {
      window.sessionStorage.setItem(key, value);
    } catch (error) {
      // Session storage may be disabled. The modal still works normally.
    }
  };

  const initOfferModal = () => {
    const modalElement = query(SELECTORS.offerModal);

    if (!modalElement || !window.bootstrap) {
      return;
    }

    const modal = window.bootstrap.Modal.getOrCreateInstance(modalElement, {
      backdrop: true,
      focus: true,
      keyboard: true,
    });

    const offerId = modalElement.dataset.offerId || 'general';
    const storageKey = `e2e-base-offer-dismissed:${offerId}`;
    const dismissed = safelyReadSession(storageKey) === '1';

    queryAll(SELECTORS.offerTriggers).forEach((trigger) => {
      trigger.addEventListener('click', (event) => {
        event.preventDefault();
        modal.show();
      });
    });

    if (!dismissed) {
      window.setTimeout(() => {
        if (!document.hidden) {
          modal.show();
        }
      }, SETTINGS.offerDelay);
    }

    modalElement.addEventListener('hidden.bs.modal', () => {
      safelyWriteSession(storageKey, '1');
    });
  };

  /* ------------------------------------------------------------------------
     Demo booking form
     ------------------------------------------------------------------------ */

  const parseResponse = async (response) => {
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
      return response.json();
    }

    const text = await response.text();
    return {
      status: response.ok ? 'success' : 'error',
      message: text,
    };
  };

  const getCsrfToken = (form) =>
    query('[name="csrfmiddlewaretoken"]', form)?.value ||
    getBody()?.dataset.csrfToken ||
    '';

  const setSubmitLoading = (button, loading) => {
    if (!button) {
      return;
    }

    if (loading) {
      if (!button.dataset.originalHtml) {
        button.dataset.originalHtml = button.innerHTML;
      }

      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      button.classList.add(CLASSES.submitLoading);
      button.innerHTML = `
        <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
        <span>Submitting...</span>
      `;
      return;
    }

    button.disabled = false;
    button.removeAttribute('aria-busy');
    button.classList.remove(CLASSES.submitLoading);

    if (button.dataset.originalHtml) {
      button.innerHTML = button.dataset.originalHtml;
    }
  };

  const initDemoForm = () => {
    const form = query(SELECTORS.demoForm);
    const body = getBody();

    if (!form || !body || form.dataset.e2eBaseBound === 'true') {
      return;
    }

    form.dataset.e2eBaseBound = 'true';

    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      const endpoint = body.dataset.demoBookingUrl;
      const csrfToken = getCsrfToken(form);
      const submitButton = query('[type="submit"]', form);

      if (!endpoint) {
        showToast(
          'The demo-booking service is unavailable. Please try again.',
          'error',
        );
        return;
      }

      setSubmitLoading(submitButton, true);

      try {
        const response = await window.fetch(endpoint, {
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: new FormData(form),
          credentials: 'same-origin',
        });

        const data = await parseResponse(response);

        if (!response.ok || data.status !== 'success') {
          throw new Error(
            data.message ||
              data.error ||
              'We could not submit your demo request.',
          );
        }

        const demoModalElement = query('#demoModal');

        if (demoModalElement && window.bootstrap) {
          const demoModal =
            window.bootstrap.Modal.getInstance(demoModalElement) ||
            window.bootstrap.Modal.getOrCreateInstance(demoModalElement);

          demoModal.hide();
        }

        form.reset();

        showToast(
          data.message ||
            "Your demo request was submitted. We'll contact you soon.",
          'success',
        );
      } catch (error) {
        showToast(
          error instanceof Error && error.message
            ? error.message
            : 'Something went wrong. Please try again.',
          'error',
        );
      } finally {
        setSubmitLoading(submitButton, false);
      }
    });
  };

  /* ------------------------------------------------------------------------
     Same-page anchors
     ------------------------------------------------------------------------ */

  const initSmoothAnchors = () => {
    queryAll('a[href*="#"]').forEach((link) => {
      link.addEventListener('click', (event) => {
        const href = link.getAttribute('href');

        if (!href || href === '#' || link.dataset.bsToggle) {
          return;
        }

        let destination;

        try {
          destination = new URL(link.href, window.location.href);
        } catch (error) {
          return;
        }

        const isSameDocument =
          destination.origin === window.location.origin &&
          destination.pathname === window.location.pathname &&
          destination.search === window.location.search;

        if (!isSameDocument || !destination.hash) {
          return;
        }

        const targetId = decodeURIComponent(destination.hash.slice(1));
        const target = document.getElementById(targetId);

        if (!target) {
          return;
        }

        event.preventDefault();

        target.scrollIntoView({
          behavior: prefersReducedMotion() ? 'auto' : 'smooth',
          block: 'start',
        });

        window.history.pushState(null, '', destination.hash);

        if (!target.hasAttribute('tabindex')) {
          target.setAttribute('tabindex', '-1');
          target.dataset.e2eBaseTemporaryTabindex = 'true';
        }

        target.focus({ preventScroll: true });

        if (target.dataset.e2eBaseTemporaryTabindex === 'true') {
          target.addEventListener(
            'blur',
            () => {
              target.removeAttribute('tabindex');
              delete target.dataset.e2eBaseTemporaryTabindex;
            },
            { once: true },
          );
        }
      });
    });
  };

  /* ------------------------------------------------------------------------
     Page transition
     ------------------------------------------------------------------------ */

  const isModifiedClick = (event) =>
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey;

  const shouldTransition = (event, link) => {
    if (
      isModifiedClick(event) ||
      link.target === '_blank' ||
      link.hasAttribute('download') ||
      link.hasAttribute('data-bs-toggle') ||
      link.hasAttribute('data-bs-dismiss') ||
      link.hasAttribute('data-offer-trigger')
    ) {
      return false;
    }

    const rawHref = link.getAttribute('href');

    if (
      !rawHref ||
      rawHref.startsWith('#') ||
      rawHref.startsWith('mailto:') ||
      rawHref.startsWith('tel:') ||
      rawHref.startsWith('javascript:')
    ) {
      return false;
    }

    let destination;

    try {
      destination = new URL(link.href, window.location.href);
    } catch (error) {
      return false;
    }

    if (destination.origin !== window.location.origin) {
      return false;
    }

    const current = new URL(window.location.href);
    const onlyHashChanged =
      destination.pathname === current.pathname &&
      destination.search === current.search &&
      destination.hash;

    return !onlyHashChanged;
  };

  const initPageTransitions = () => {
    const body = getBody();

    if (!body || prefersReducedMotion()) {
      return;
    }

    document.addEventListener('click', (event) => {
      const link = event.target.closest('a[href]');

      if (!link || !shouldTransition(event, link)) {
        return;
      }

      event.preventDefault();
      body.classList.add(CLASSES.pageLeaving);

      window.setTimeout(() => {
        window.location.assign(link.href);
      }, SETTINGS.pageTransitionDuration);
    });

    window.addEventListener('pageshow', () => {
      body.classList.remove(CLASSES.pageLeaving);
    });
  };

  /* ------------------------------------------------------------------------
     Public base API for page-specific scripts
     ------------------------------------------------------------------------ */

  const showFeedback = (
    message,
    type = 'success',
    kind = 'auto',
  ) => {
    if (
      window.E2EFeedback &&
      typeof window.E2EFeedback.show === 'function'
    ) {
      window.E2EFeedback.show({
        message,
        type,
        kind,
      });
      return;
    }

    showToast(message, type);
  };

  window.E2EBase = Object.freeze({
    showToast,
    showFeedback,
  });

  /* ------------------------------------------------------------------------
     Initialize
     ------------------------------------------------------------------------ */

  ready(() => {
    initAos();
    initNavbar();
    initDjangoMessages();
    initOfferModal();
    initDemoForm();
    initSmoothAnchors();
    initPageTransitions();
  });
})();
