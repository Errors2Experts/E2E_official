/**
 * Errors2Experts — Animated Form / Request Feedback
 * File: main/static/js/e2e-feedback.js
 */
(() => {
    "use strict";

    const DEFAULT_DURATION = 5600;

    const overlay =
        () => document.getElementById(
            "e2eFeedbackOverlay"
        );

    const card =
        () => document.getElementById(
            "e2eFeedbackCard"
        );

    const title =
        () => document.getElementById(
            "e2eFeedbackTitle"
        );

    const eyebrow =
        () => document.getElementById(
            "e2eFeedbackEyebrow"
        );

    const message =
        () => document.getElementById(
            "e2eFeedbackMessage"
        );

    const nextText =
        () => document.getElementById(
            "e2eFeedbackNextText"
        );

    const progress =
        () => document.getElementById(
            "e2eFeedbackProgress"
        );

    const closeButton =
        () => document.getElementById(
            "e2eFeedbackClose"
        );

    const doneButton =
        () => document.getElementById(
            "e2eFeedbackDone"
        );


    let closeTimer = null;
    let queue = [];
    let active = false;


    const clean = (value) =>
        String(value || "")
            .replace(/\s+/g, " ")
            .trim();


    const normalizedType = (type) => {

        const value =
            clean(type).toLowerCase();

        if (
            value.includes("error") ||
            value.includes("danger")
        ) {
            return "error";
        }

        if (value.includes("warning")) {
            return "warning";
        }

        if (value.includes("success")) {
            return "success";
        }

        return "info";
    };


    const detectKind = (
        text,
        requestedKind = "auto"
    ) => {

        if (
            requestedKind &&
            requestedKind !== "auto"
        ) {
            return requestedKind;
        }

        const value =
            clean(text).toLowerCase();


        if (
            value.includes("registration") ||
            value.includes("registered")
        ) {
            return "registration";
        }


        if (
            value.includes("demo sent")
        ) {
            return "demo_sent";
        }


        if (
            value.includes("demo") ||
            value.includes("request") ||
            value.includes("requirement") ||
            value.includes("service")
        ) {
            return "request";
        }


        if (
            value.includes("application") ||
            value.includes("applied")
        ) {
            return "application";
        }


        if (
            value.includes("booking") ||
            value.includes("booked")
        ) {
            return "booking";
        }


        if (
            value.includes("message") ||
            value.includes("enquiry") ||
            value.includes("contact")
        ) {
            return "message";
        }


        return "generic";
    };


    const feedbackCopy = (
        kind,
        type
    ) => {

        if (type === "error") {
            return {
                eyebrow:
                    "PLEASE CHECK",
                title:
                    "Something Needs Attention",
                next:
                    "Review the information shown above and try again.",
            };
        }


        const copies = {

            registration: {
                eyebrow:
                    "REGISTRATION RECEIVED",
                title:
                    "Registration Successful!",
                next:
                    "Your details are safely received. We’ll keep you updated with the next steps.",
            },

            request: {
                eyebrow:
                    "REQUEST RECEIVED",
                title:
                    "Request Submitted!",
                next:
                    "Our team will review your request and contact you shortly.",
            },

            demo_sent: {
                eyebrow:
                    "DEMO READY",
                title:
                    "Demo Sent Successfully!",
                next:
                    "Please check your email for the requested demo link and access details.",
            },

            application: {
                eyebrow:
                    "APPLICATION RECEIVED",
                title:
                    "Application Submitted!",
                next:
                    "Our team will review your profile and contact you if you are shortlisted.",
            },

            booking: {
                eyebrow:
                    "BOOKING RECEIVED",
                title:
                    "Booking Successful!",
                next:
                    "Your booking is received. Follow the next payment or confirmation step shown on the website.",
            },

            message: {
                eyebrow:
                    "MESSAGE RECEIVED",
                title:
                    "Message Sent Successfully!",
                next:
                    "Thank you for contacting us. Our team will get back to you shortly.",
            },

            generic: {
                eyebrow:
                    "SUBMITTED SUCCESSFULLY",
                title:
                    "Successfully Submitted!",
                next:
                    "Thank you. Your information has been received by the Errors2Experts team.",
            },

        };


        return (
            copies[kind] ||
            copies.generic
        );
    };


    const animateTitle = (
        titleText
    ) => {

        const titleElement =
            title();

        if (!titleElement) {
            return;
        }

        titleElement.innerHTML = "";

        clean(titleText)
            .split(" ")
            .forEach(
                (word, index) => {

                    const span =
                        document.createElement(
                            "span"
                        );

                    span.className =
                        "e2e-feedback-title-word";

                    span.textContent =
                        word;

                    span.style.animationDelay =
                        `${250 + index * 90}ms`;

                    titleElement.appendChild(
                        span
                    );

                }
            );

    };


    const resetAnimations = () => {

        const cardElement =
            card();

        const progressElement =
            progress();

        if (cardElement) {

            cardElement.classList.remove(
                "is-error"
            );

        }

        if (progressElement) {

            progressElement.classList.remove(
                "is-running"
            );

            // Force restart of CSS animation.
            void progressElement.offsetWidth;

        }

    };


    const close = () => {

        const overlayElement =
            overlay();

        if (!overlayElement) {
            return;
        }


        if (closeTimer) {

            window.clearTimeout(
                closeTimer
            );

            closeTimer = null;

        }


        overlayElement.classList.remove(
            "is-visible"
        );

        overlayElement.setAttribute(
            "aria-hidden",
            "true"
        );


        document.body.classList.remove(
            "e2e-feedback-open"
        );


        active = false;


        window.setTimeout(
            () => {

                if (queue.length) {

                    showNext();

                }

            },
            280
        );

    };


    const showOne = ({
        message: rawMessage,
        type = "success",
        kind = "auto",
        duration = DEFAULT_DURATION,
    }) => {

        const overlayElement =
            overlay();

        const cardElement =
            card();

        if (
            !overlayElement ||
            !cardElement
        ) {
            return false;
        }


        const cleanMessage =
            clean(rawMessage);


        if (!cleanMessage) {
            return false;
        }


        const safeType =
            normalizedType(type);

        const detectedKind =
            detectKind(
                cleanMessage,
                kind
            );

        const copy =
            feedbackCopy(
                detectedKind,
                safeType
            );


        resetAnimations();


        cardElement.classList.toggle(
            "is-error",
            safeType === "error"
        );


        if (eyebrow()) {

            eyebrow().textContent =
                copy.eyebrow;

        }


        animateTitle(
            copy.title
        );


        if (message()) {

            message().textContent =
                cleanMessage;

        }


        if (nextText()) {

            nextText().textContent =
                copy.next;

        }


        const progressElement =
            progress();

        if (progressElement) {

            progressElement.style
                .setProperty(
                    "--e2e-feedback-duration",
                    `${duration}ms`
                );

        }


        overlayElement.classList.add(
            "is-visible"
        );

        overlayElement.setAttribute(
            "aria-hidden",
            "false"
        );


        document.body.classList.add(
            "e2e-feedback-open"
        );


        active = true;


        window.requestAnimationFrame(
            () => {

                if (progressElement) {

                    progressElement.classList.add(
                        "is-running"
                    );

                }

                cardElement.focus({
                    preventScroll: true,
                });

            }
        );


        if (
            Number.isFinite(duration) &&
            duration > 0
        ) {

            closeTimer =
                window.setTimeout(
                    close,
                    duration
                );

        }


        return true;

    };


    const showNext = () => {

        if (
            active ||
            !queue.length
        ) {
            return;
        }


        const item =
            queue.shift();

        showOne(
            item
        );

    };


    const show = (
        optionsOrMessage,
        type = "success",
        kind = "auto"
    ) => {

        const item =
            typeof optionsOrMessage ===
            "object"
                ? {
                    message:
                        optionsOrMessage.message,
                    type:
                        optionsOrMessage.type ||
                        "success",
                    kind:
                        optionsOrMessage.kind ||
                        "auto",
                    duration:
                        Number.isFinite(
                            optionsOrMessage.duration
                        )
                            ? optionsOrMessage.duration
                            : DEFAULT_DURATION,
                }
                : {
                    message:
                        optionsOrMessage,
                    type,
                    kind,
                    duration:
                        DEFAULT_DURATION,
                };


        queue.push(
            item
        );


        showNext();

    };


    const readDjangoMessages = () => {

        const queueElement =
            document.getElementById(
                "e2eFeedbackQueue"
            );


        if (!queueElement) {
            return;
        }


        queueElement
            .querySelectorAll(
                ".e2e-feedback-queued-message"
            )
            .forEach(
                (element) => {

                    const rawTags =
                        element.dataset.tags ||
                        "info";

                    const rawMessage =
                        element.dataset.message ||
                        "";


                    show({
                        message:
                            rawMessage,

                        type:
                            normalizedType(
                                rawTags
                            ),

                        kind:
                            "auto",
                    });

                }
            );


        queueElement.remove();

    };


    const initEvents = () => {

        const overlayElement =
            overlay();

        const cardElement =
            card();


        closeButton()?.addEventListener(
            "click",
            close
        );


        doneButton()?.addEventListener(
            "click",
            close
        );


        overlayElement?.addEventListener(
            "click",
            (event) => {

                if (
                    event.target ===
                    overlayElement
                ) {
                    close();
                }

            }
        );


        document.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Escape" &&
                    active
                ) {
                    close();
                }

            }
        );


        cardElement?.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();
            }
        );

    };


    const ready = (
        callback
    ) => {

        if (
            document.readyState ===
            "loading"
        ) {

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


    window.E2EFeedback =
        Object.freeze({
            show,
            close,
        });


    // Helpful global alias for older page scripts.
    // Existing AJAX forms that call showToast(..., "success")
    // now receive the same animated success UI.
    window.showE2EFeedback =
        show;


    ready(
        () => {

            initEvents();

            readDjangoMessages();

        }
    );

})();
