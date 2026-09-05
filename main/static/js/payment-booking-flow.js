/**
 * Errors2Experts — Shared Payment Booking Flow
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
                }
            );
            return;
        }

        callback();
    };


    ready(() => {

        const paymentFlow =
            document.getElementById(
                "e2ePaymentFlow"
            );

        const qrTarget =
            document.querySelector(
                ".e2e-payment-qr-highlight-target"
            );


        if (!paymentFlow) {
            return;
        }


        window.requestAnimationFrame(
            () => {

                paymentFlow.classList.add(
                    "is-ready"
                );

            }
        );


        if (qrTarget) {

            window.setTimeout(
                () => {

                    qrTarget.classList.add(
                        "e2e-qr-ready-highlight"
                    );

                },
                1450
            );


            window.setTimeout(
                () => {

                    qrTarget.classList.remove(
                        "e2e-qr-ready-highlight"
                    );

                },
                3100
            );

        }

    });

})();
