/**
 * Errors2Experts — Our Team filters
 *
 * Multi-role behavior:
 *
 * Employee:
 *   Development -> Software Developer
 *   Trainers     -> Python Trainer
 *
 * Selecting Development:
 *   Employee stays visible and card role becomes Software Developer.
 *
 * Selecting Trainers:
 *   Same employee stays visible and card role becomes Python Trainer.
 *
 * Selecting All Members:
 *   Card shows the employee's first role as the headline and
 *   all assigned roles as chips.
 */

(() => {
    "use strict";


    const ready = (callback) => {

        if (document.readyState === "loading") {

            document.addEventListener(
                "DOMContentLoaded",
                callback,
                {
                    once: true,
                },
            );

            return;
        }

        callback();
    };


    ready(() => {

        const filterButtons = Array.from(
            document.querySelectorAll(
                "[data-team-filter]",
            ),
        );


        const memberCards = Array.from(
            document.querySelectorAll(
                "[data-team-member]",
            ),
        );


        const emptyState =
            document.getElementById(
                "teamFilterEmpty",
            );


        if (
            !filterButtons.length ||
            !memberCards.length
        ) {
            return;
        }


        const readRoles = (card) => {           
            return Array.from(
                card.querySelectorAll(
                    "[data-role-category]",
                ),
            ).map(
                (roleElement) => ({
                    category:
                        roleElement.dataset.roleCategory || "",

                    categoryName:
                        roleElement.dataset.roleCategoryName || "",

                    title:
                        roleElement.dataset.roleTitle || "Team Member",

                    description:
                        roleElement.dataset.roleDescription || "",
                }),
            );

        };


        const animateRoleChange = (
            roleElement,
            newText,
        ) => {

            if (!roleElement) {
                return;
            }


            if (
                roleElement.textContent.trim() ===
                newText
            ) {
                return;
            }


            roleElement.classList.add(
                "is-changing",
            );


            window.setTimeout(
                () => {

                    roleElement.textContent =
                        newText;

                    roleElement.classList.remove(
                        "is-changing",
                    );

                },
                140,
            );

        };


        const showCard = (
            card,
            filter,
        ) => {

            const roles =
                readRoles(card);


            const currentRole =
                card.querySelector(
                    "[data-current-role]",
                );
            
            const currentDescription =
                card.querySelector(
                    "[data-current-description]",
                );

            const chips =
                card.querySelector(
                    "[data-role-chips]",
                );


            if (filter === "all") {

                card.hidden = false;

                card.classList.remove(
                    "is-filtering-out",
                );


                const firstRole =
                    roles[0]?.title ||
                    "Team Member";

                const firstDescription =
                    roles[0]?.description ||
                    "Contributing to the growth and success of Errors2Experts.";    

                animateRoleChange(
                    currentRole,
                    firstRole,
                );

                animateRoleChange(
                    currentDescription,
                    firstDescription,
                );

                if (chips) {
                    chips.hidden = false;
                }


                return true;
            }


            const matchingRole =
                roles.find(
                    (role) =>
                        role.category === filter,
                );


            if (!matchingRole) {

                card.classList.add(
                    "is-filtering-out",
                );


                window.setTimeout(
                    () => {

                        if (
                            card.classList.contains(
                                "is-filtering-out",
                            )
                        ) {
                            card.hidden = true;
                        }

                    },
                    210,
                );


                return false;
            }


            card.hidden = false;


            window.requestAnimationFrame(
                () => {

                    card.classList.remove(
                        "is-filtering-out",
                    );

                },
            );


            animateRoleChange(
                currentRole,
                matchingRole.title,
            );

            animateRoleChange(
                currentDescription,
                matchingRole.description ||
                "Contributing to the growth and success of Errors2Experts.",
            );


            if (chips) {
                chips.hidden = true;
            }


            return true;
        };


        const applyFilter = (filter) => {

            let visibleCount = 0;


            memberCards.forEach(
                (card) => {

                    if (
                        showCard(
                            card,
                            filter,
                        )
                    ) {
                        visibleCount += 1;
                    }

                },
            );


            if (emptyState) {

                emptyState.hidden =
                    visibleCount !== 0;

            }

        };


        filterButtons.forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    () => {

                        const filter =
                            button.dataset.teamFilter ||
                            "all";


                        filterButtons.forEach(
                            (otherButton) => {

                                const isCurrent =
                                    otherButton ===
                                    button;


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


                        applyFilter(
                            filter,
                        );

                    },
                );

            },
        );


        // Ensure the initial All Members state is consistent.
        applyFilter(
            "all",
        );

    });

})();
