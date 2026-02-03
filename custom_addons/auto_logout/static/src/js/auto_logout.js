odoo.define('auto_logout.AutoLogout', function (require) {
    "use strict";
    console.log('auto_logout: define loaded');

    var WebClient = require('web.WebClient');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var _t = core._t;
    var session = require('web.session');

    WebClient.include({
        init: function () {
            console.log('auto_logout: WebClient.init called');
            this._super.apply(this, arguments);
            this._autoLogoutSetup();
        },

        start: function () {
            console.log('auto_logout: WebClient.start called');
            var self = this;
            console.log('auto_logout: WebClient.start called 2.2');
            return this._super.apply(this, arguments).then(function () {
                self._autoLogoutSetup();
            });
        },

        _autoLogoutSetup: function () {
            console.log('auto_logout: _autoLogoutSetup');
            var self = this;
            var timeoutMinutes = 30; // valeur par défaut

            // lire le paramètre système web.auto_logout_minutes
            rpc.query({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: ['web.auto_logout_minutes', false],
            }).then(function (value) {
                console.log('auto_logout: got param value:', value);
                if (value) {
                    var parsed = parseInt(value, 10);
                    if (!isNaN(parsed) && parsed > 0) {
                        timeoutMinutes = parsed;
                        console.log('auto_logout: parsed value:', timeoutMinutes);
                    }
                }
                console.log('auto_logout: timeoutMinutes:', timeoutMinutes);
                if (!timeoutMinutes || timeoutMinutes <= 0) {
                    console.log('auto_logout: timeout disabled or invalid');
                    return;
                }
                console.log('auto_logout: calling _startIdleTimer with', timeoutMinutes);
                self._startIdleTimer(timeoutMinutes);
            }).catch(function (error) {
                console.log('auto_logout: error reading param', error);
            });
        },

        _startIdleTimer: function (minutes) {
            console.log('auto_logout: start idle timer', minutes, 'minutes');
            var self = this;
            var idleMs = minutes * 60 * 1000;
            var warnBeforeMs = 30 * 1000; // avertir 30 secondes avant
            var warnTimer = null;
            var logoutTimer = null;
            var warnDialog = null;
            var dialogActive = false;

            function clearAll() {
                if (warnTimer) { clearTimeout(warnTimer); warnTimer = null; }
                if (logoutTimer) { clearTimeout(logoutTimer); logoutTimer = null; }
                if (warnDialog) { try { warnDialog.close(); } catch (e) { } warnDialog = null; }
                dialogActive = false;
            }

            function doLogout() {
                console.log('auto_logout: doLogout called');
                clearAll();
                // Arrêter la détection d'activité
                ['mousemove', 'keydown', 'click', 'touchstart'].forEach(function (ev) {
                    document.removeEventListener(ev, resetTimer);
                });
                // Faire la déconnexion via la session
                session.session_logout().then(function () {
                    window.location.href = '/web/login';
                }).catch(function (error) {
                    console.log('auto_logout: logout error', error);
                    window.location.href = '/web/login';
                });
            }

            function showWarning() {
                console.log('auto_logout: showWarning called');
                if (warnDialog) {
                    try { warnDialog.close(); } catch (e) { }
                }
                dialogActive = true;

                var safeClose = function () {
                    console.log('auto_logout: dialog closed');
                    if (warnDialog) {
                        try { warnDialog.close(); } catch (e) { console.log('auto_logout: close error', e); }
                        warnDialog = null;
                    }
                    dialogActive = false;
                    resetTimer();
                };

                warnDialog = new Dialog(self, {
                    title: _t("Déconnexion pour inactivité"),
                    size: 'small',
                    $content: $('<div/>').text(_t('Vous serez déconnecté dans 30 secondes en raison de l\'inactivité. Cliquez sur "Rester connecté" pour annuler.')),
                    buttons: [
                        {
                            text: _t('Rester connecté'),
                            classes: 'btn-primary',
                            click: function () {
                                console.log('auto_logout: button clicked');
                                safeClose();
                            },
                        },
                    ],
                });

                warnDialog.open();

                // Attendre que le modal soit affiché
                setTimeout(function () {
                    if (warnDialog && warnDialog.$modal) {
                        warnDialog.$modal.find('.modal-header .btn-close, .modal-header .close').on('click', function (e) {
                            e.preventDefault();
                            safeClose();
                        });
                    }
                }, 100);
            }

            function resetTimer() {
                // Ne pas réinitialiser si le dialog d'avertissement est affiché
                if (dialogActive) {
                    return;
                }
                clearAll();
                var warnAt = Math.max(idleMs - warnBeforeMs, 0);
                warnTimer = setTimeout(showWarning, warnAt);
                logoutTimer = setTimeout(doLogout, idleMs);
            }

            // événements d'activité pour réinitialiser le timer
            ['mousemove', 'keydown', 'click', 'touchstart'].forEach(function (ev) {
                document.addEventListener(ev, resetTimer, { passive: true });
            });

            // démarrer
            resetTimer();
        },
    });
});