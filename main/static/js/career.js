(() => {
    "use strict";


    const ready = (callback) => {

        if (document.readyState === "loading") {

            document.addEventListener(
                "DOMContentLoaded",
                callback,
                { once: true },
            );

            return;
        }

        callback();
    };


    ready(() => {

        const buttons = Array.from(
            document.querySelectorAll(
                "[data-career-filter]",
            ),
        );


        const cards = Array.from(
            document.querySelectorAll(
                "[data-career-card]",
            ),
        );


        const searchInput =
            document.getElementById(
                "careerSearch",
            );


        const emptyState =
            document.getElementById(
                "careerFilterEmpty",
            );


        if (!cards.length) {
            return;
        }


        let activeFilter = "all";


        const normalise = (value) => {
            return String(value || "")
                .trim()
                .toLowerCase();
        };


        const applyFilters = () => {

            const query =
                normalise(
                    searchInput?.value,
                );


            let visibleCount = 0;


            cards.forEach((card) => {

                const employment =
                    normalise(
                        card.dataset.employment,
                    );


                const searchText =
                    normalise(
                        card.dataset.search,
                    );


                const typeMatches =
                    activeFilter === "all" ||
                    employment === activeFilter;


                const searchMatches =
                    !query ||
                    searchText.includes(query);


                const visible =
                    typeMatches &&
                    searchMatches;


                card.hidden =
                    !visible;


                if (visible) {
                    visibleCount += 1;
                }

            });


            if (emptyState) {

                emptyState.hidden =
                    visibleCount !== 0;

            }

        };


        buttons.forEach((button) => {

            button.addEventListener(
                "click",
                () => {

                    activeFilter =
                        normalise(
                            button.dataset.careerFilter,
                        ) || "all";


                    buttons.forEach(
                        (otherButton) => {

                            const isCurrent =
                                otherButton === button;


                            otherButton.classList.toggle(
                                "is-active",
                                isCurrent,
                            );


                            otherButton.setAttribute(
                                "aria-pressed",
                                isCurrent
                                    ? "true"
                                    : "false",
                            );

                        },
                    );


                    applyFilters();

                },
            );

        });


        searchInput?.addEventListener(
            "input",
            applyFilters,
        );


        applyFilters();

    });

})();

/* ============================================================
   CAREER APPLICATION MODAL + AJAX SUBMISSION
============================================================ */
(() => {
  "use strict";
  const init = () => {
    const modal = document.getElementById("careerApplicationModal");
    const form = document.getElementById("careerApplicationForm");
    if (!modal || !form) return;

    const formState = document.getElementById("careerApplicationFormState");
    const successState = document.getElementById("careerApplicationSuccess");
    const successMessage = document.getElementById("careerApplicationSuccessMessage");
    const alertBox = document.getElementById("careerApplicationError");
    const submit = document.getElementById("careerApplicationSubmit");
    const normal = submit?.querySelector(".career-submit-normal");
    const loading = submit?.querySelector(".career-submit-loading");
    const resume = document.getElementById("career_resume");
    const resumeLabel = document.getElementById("careerResumeLabel");

    const clearErrors = () => {
      if (alertBox) alertBox.hidden = true;
      form.querySelectorAll(".career-form-group.has-error").forEach(el => el.classList.remove("has-error"));
      form.querySelectorAll("[data-error-for]").forEach(el => el.textContent = "");
    };

    const fieldError = (name, messages) => {
      const field = form.elements[name];
      const err = form.querySelector(`[data-error-for="${name}"]`);
      field?.closest(".career-form-group")?.classList.add("has-error");
      if (err) err.textContent = (Array.isArray(messages) ? messages : [messages]).filter(Boolean).join(" ");
    };

    const setLoading = (state) => {
      if (!submit) return;
      submit.disabled = state;
      if (normal) normal.hidden = state;
      if (loading) loading.hidden = !state;
    };

    const reset = () => {
      form.reset(); clearErrors(); setLoading(false);
      if (resumeLabel) resumeLabel.textContent = "Choose your resume";
      if (formState) formState.hidden = false;
      if (successState) successState.hidden = true;
    };

    resume?.addEventListener("change", () => {
      if (resumeLabel) resumeLabel.textContent = resume.files?.[0]?.name || "Choose your resume";
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault(); clearErrors();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      setLoading(true);
      try {
        const response = await fetch(form.action, {
          method: "POST", body: new FormData(form),
          headers: {"X-Requested-With": "XMLHttpRequest"}, credentials: "same-origin"
        });
        let data = {};
        try { data = await response.json(); } catch (_) {}
        if (!response.ok || data.status !== "success") {
          Object.entries(data.errors || {}).forEach(([name, messages]) => fieldError(name, messages));
          if (alertBox) {
            alertBox.hidden = false;
            const t = alertBox.querySelector("span");
            if (t) t.textContent = data.message || "Please check the highlighted fields and try again.";
          }
          form.querySelector(".career-form-group.has-error")?.scrollIntoView({behavior:"smooth",block:"center"});
          return;
        }
        if (formState) formState.hidden = true;
        if (successState) successState.hidden = false;
        if (successMessage && data.message) successMessage.textContent = data.message;
      } catch (error) {
        console.error("Career application submission failed:", error);
        if (alertBox) {
          alertBox.hidden = false;
          const t = alertBox.querySelector("span");
          if (t) t.textContent = "We couldn't submit your application right now. Please check your connection and try again.";
        }
      } finally { setLoading(false); }
    });

    modal.addEventListener("hidden.bs.modal", () => window.setTimeout(reset, 100));
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, {once:true}); else init();
})();

