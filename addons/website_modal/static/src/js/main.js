//License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

odoo.define('website_modal.main', function(require) {
    "use strict";

    function show_modal(type, modal) {
        if (modal.attr('data-' + String(type) + '-once')) {
            var key = String(type) + String(modal.attr('id'));
            if (localStorage.getItem(key) == null) {
                localStorage.setItem(key, 1);
                modal.modal();
            }
        } else {
            modal.modal();
        }
    }

    $(document).ready(function() {

        // Visit Page
        $('.wpopup[data-visit="True"][data-visit-url="' + location.pathname + '"], .wpopup[data-visit="True"][data-visit-url="*"]').each(function() {
            show_modal('visit', $(this));
        });

        // Time on Page
        $('.wpopup[data-time="True"][data-time-url="' + location.pathname + '"], .wpopup[data-time="True"][data-time-url="*"]').each(function() {
            var ms = Number($(this).attr('data-time-val')) * 1000;
            var modal = $(this);
            setTimeout(function() {
                show_modal('time', modal);
            }, ms);
        });

        // Scroll to bottom
        $(window).scroll(function() {
            var hT = $('#wrapwrap > footer').offset().top,
                hH = $('#wrapwrap > footer').outerHeight(),
                wH = $(window).height(),
                wS = $(this).scrollTop();
            if (wS >= (hT + hH - wH)) {
                $('.wpopup[data-scroll="True"][data-scroll-url="' + location.pathname + '"], .wpopup[data-scroll="True"][data-scroll-url="*"]').each(function() {
                    show_modal('scroll', $(this));
                });
            }
        });
    });

    // Page Exit Intent
    function addEvent(obj, evt, fn) {
        if (obj.addEventListener) {
            obj.addEventListener(evt, fn, false);
        } else if (obj.attachEvent) {
            obj.attachEvent("on" + evt, fn);
        }
    }
    addEvent(document, 'mouseout', function(evt) {
        if (evt.toElement == null && evt.relatedTarget == null) {
            $('.wpopup[data-exit="True"][data-exit-url="' + location.pathname + '"], .wpopup[data-exit="True"][data-exit-url="*"]').each(function() {
                show_modal('exit', $(this));
            });
        };
    });
});
