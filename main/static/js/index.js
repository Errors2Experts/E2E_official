(function () {
  'use strict';

  function onReady(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback, { once: true });
      return;
    }

    callback();
  }

  function getHomePage() {
    return document.querySelector('.e2e-home-page');
  }

  /* =======================================================
     HERO INTRO
     Replays whenever the page is visited or restored from
     browser history without changing the existing design.
     ======================================================= */

  function replayHomeIntro() {
    var page = getHomePage();

    if (!page) {
      return;
    }

    var animatedElements = page.querySelectorAll(
      '.e2e-home-intro-card, ' +
      '.e2e-home-intro-actions, ' +
      '.e2e-home-intro-badges'
    );

    animatedElements.forEach(function (element) {
      element.classList.remove('is-animating');
    });

    /* Force a new animation timeline. */
    void page.offsetWidth;

    animatedElements.forEach(function (element) {
      element.classList.add('is-animating');
    });
  }


  /* =======================================================
     WORKSHOP REGISTRATION CONDITIONAL FIELDS + VALIDATION
     ======================================================= */

  function initializeWorkshopRegistration() {
    var form = document.getElementById('e2eHomeWorkshopRegistrationForm');

    if (!form) {
      return;
    }

    var otherDomainCheckbox = document.getElementById('domain16');
    var otherDomainContainer = document.getElementById('otherInterestDomainDiv');
    var otherDomainInput = otherDomainContainer
      ? otherDomainContainer.querySelector('input[name="other_domain"]')
      : null;

    var technicalSkillSelect = document.getElementById('technicalSkillSelect');
    var technicalSkillContainer = document.getElementById('otherTechnicalSkillDiv');
    var technicalSkillInput = technicalSkillContainer
      ? technicalSkillContainer.querySelector('input[name="technical_skill_other"]')
      : null;

    function updateOtherDomainField() {
      if (!otherDomainCheckbox || !otherDomainContainer) {
        return;
      }

      var showField = otherDomainCheckbox.checked;
      otherDomainContainer.classList.toggle('d-none', !showField);

      if (otherDomainInput) {
        otherDomainInput.required = showField;
        if (!showField) {
          otherDomainInput.value = '';
        }
      }
    }

    function updateTechnicalSkillField() {
      if (!technicalSkillSelect || !technicalSkillContainer) {
        return;
      }

      var showField = technicalSkillSelect.value === 'Other';
      technicalSkillContainer.classList.toggle('d-none', !showField);

      if (technicalSkillInput) {
        technicalSkillInput.required = showField;
        if (!showField) {
          technicalSkillInput.value = '';
        }
      }
    }

    if (otherDomainCheckbox) {
      otherDomainCheckbox.addEventListener('change', updateOtherDomainField);
      updateOtherDomainField();
    }

    if (technicalSkillSelect) {
      technicalSkillSelect.addEventListener('change', updateTechnicalSkillField);
      updateTechnicalSkillField();
    }

    form.addEventListener('submit', function (event) {
      var selectedDomains = form.querySelectorAll(
        'input[name="interested_domains"]:checked'
      );

      var selectedDemoTimes = form.querySelectorAll(
        'input[name="preferred_demo_time"]:checked'
      );

      if (selectedDomains.length === 0) {
        event.preventDefault();
        window.alert('Please select at least one Interested Domain.');

        var firstDomain = form.querySelector('input[name="interested_domains"]');
        if (firstDomain) {
          firstDomain.focus();
        }
        return;
      }

      if (selectedDemoTimes.length === 0) {
        event.preventDefault();
        window.alert('Please select at least one preferred demo time.');

        var firstTime = form.querySelector('input[name="preferred_demo_time"]');
        if (firstTime) {
          firstTime.focus();
        }
      }
    });
  }

  /* =======================================================
     SERVICE MODAL SUPPORT
     Uses data-service-name if registration buttons are
     enabled again in the future—no inline onclick required.
     ======================================================= */

  function initializeServiceBookingButtons() {
    var serviceNameInput = document.getElementById('serviceNameInput');

    if (!serviceNameInput) {
      return;
    }

    document.querySelectorAll('[data-service-name]').forEach(function (button) {
      button.addEventListener('click', function () {
        serviceNameInput.value = button.dataset.serviceName || '';
      });
    });
  }

  onReady(function () {
    replayHomeIntro();
    initializeWorkshopRegistration();
    initializeServiceBookingButtons();
  });

  window.addEventListener('pageshow', replayHomeIntro);
})();
