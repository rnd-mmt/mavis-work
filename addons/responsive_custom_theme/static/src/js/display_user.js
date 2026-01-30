odoo.define('responsive_custom_theme.display_user_info', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var session = require('web.session');

    var DisplayUserInfo = Widget.extend({
        template: 'display_user_info',

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return session.user_info;
            }).then(function (user) {
                self.$('.user-info-container').replaceWith(self.renderElement(user));
            });
        },
    });

    return DisplayUserInfo;
});
