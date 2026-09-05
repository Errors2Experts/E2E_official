(() => {
    "use strict";


    const ready = (callback) => {

        if (document.readyState === "loading") {

            document.addEventListener(
                "DOMContentLoaded",
                callback,
                {
                    once: true,
                }
            );

            return;
        }


        callback();

    };


    ready(() => {


        const body =
            document.body;


        const toggle =
            document.getElementById(
                "e2eSidebarToggle"
            );


        const sidebar =
            document.getElementById(
                "nav-sidebar"
            );


        const overlay =
            document.getElementById(
                "e2eSidebarOverlay"
            );


        const desktopQuery =
            window.matchMedia(
                "(min-width: 901px)"
            );


        const storageKey =
            "e2e-admin-sidebar-collapsed";


        /* =====================================================
           DESKTOP COLLAPSE
        ====================================================== */

        const loadDesktopState = () => {

            if (!desktopQuery.matches) {
                return;
            }


            let collapsed =
                false;


            try {

                collapsed =
                    window.localStorage
                        .getItem(
                            storageKey
                        ) === "1";

            } catch (error) {

                collapsed =
                    false;

            }


            body.classList.toggle(
                "e2e-sidebar-collapsed",
                collapsed
            );


            if (toggle) {

                toggle.setAttribute(
                    "aria-expanded",
                    collapsed
                        ? "false"
                        : "true"
                );

            }

        };


        const toggleDesktopSidebar = () => {

            const collapsed =
                body.classList.toggle(
                    "e2e-sidebar-collapsed"
                );


            if (toggle) {

                toggle.setAttribute(
                    "aria-expanded",
                    collapsed
                        ? "false"
                        : "true"
                );

            }


            try {

                window.localStorage
                    .setItem(
                        storageKey,
                        collapsed
                            ? "1"
                            : "0"
                    );

            } catch (error) {

                // Storage is optional.
            }

        };


        /* =====================================================
           MOBILE DRAWER
        ====================================================== */

        const openMobileSidebar = () => {

            body.classList.add(
                "e2e-sidebar-open"
            );


            if (toggle) {

                toggle.setAttribute(
                    "aria-expanded",
                    "true"
                );

            }

        };


        const closeMobileSidebar = () => {

            body.classList.remove(
                "e2e-sidebar-open"
            );


            if (toggle) {

                toggle.setAttribute(
                    "aria-expanded",
                    "false"
                );

            }

        };


        const toggleMobileSidebar = () => {

            if (
                body.classList.contains(
                    "e2e-sidebar-open"
                )
            ) {

                closeMobileSidebar();

            } else {

                openMobileSidebar();

            }

        };


        /* =====================================================
           TOGGLE BUTTON
        ====================================================== */

        if (toggle) {

            toggle.addEventListener(
                "click",
                () => {

                    if (desktopQuery.matches) {

                        toggleDesktopSidebar();

                    } else {

                        toggleMobileSidebar();

                    }

                }
            );

        }


        if (overlay) {

            overlay.addEventListener(
                "click",
                closeMobileSidebar
            );

        }


        document.addEventListener(
            "keydown",
            (event) => {

                if (event.key === "Escape") {

                    closeMobileSidebar();

                }

            }
        );


        /* =====================================================
           CLOSE MOBILE DRAWER AFTER NAVIGATION
        ====================================================== */

        if (sidebar) {

            sidebar
                .querySelectorAll(
                    "a"
                )
                .forEach(
                    (link) => {

                        link.addEventListener(
                            "click",
                            () => {

                                if (
                                    !desktopQuery.matches
                                ) {

                                    closeMobileSidebar();

                                }

                            }
                        );

                    }
                );

        }


        /* =====================================================
           RESPONSIVE STATE
        ====================================================== */

        const handleBreakpoint = () => {

            if (desktopQuery.matches) {

                closeMobileSidebar();

                loadDesktopState();

            } else {

                body.classList.remove(
                    "e2e-sidebar-collapsed"
                );

                if (toggle) {

                    toggle.setAttribute(
                        "aria-expanded",
                        "false"
                    );

                }

            }

        };


        if (
            typeof desktopQuery
                .addEventListener === "function"
        ) {

            desktopQuery.addEventListener(
                "change",
                handleBreakpoint
            );

        }


        handleBreakpoint();

    });

})();
