odoo.define('maintenance_contract.timer', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var time = require('web.time');

    var _t = core._t;

    console.log('mandeha ny widget intervention');

    var TimeCounter = AbstractField.extend({

        willStart: function () {
            var self = this;
            var def = this._rpc({
                model: 'account.analytic.line',
                method: 'search_read',
                domain: [['task_id', '=', this.res_id], ['user_id', '=', self.record.context['uid']]],
            }).then(function (result) {
                if (self.mode === 'readonly') {
                    var currentDate = new Date();
                    self.duration = 0;
                    _.each(result, function (data) {
                        self.duration += data.date_end ?
                            self._getDateDifference(data.date_start, data.date_end) :
                            self._getDateDifference(time.auto_str_to_date(data.date_start), currentDate);
                    });
                }
            });
            return $.when(this._super.apply(this, arguments), def);
        },

        destroy: function () {
            this._super.apply(this, arguments);
            clearTimeout(this.timer);
        },

        isSet: function () {
            return true;
        },

        _getDateDifference: function (dateStart, dateEnd) {
            return moment(dateEnd).diff(moment(dateStart));
        },

        _render: function () {
            this._startTimeCounter();
//            this._startIdleCounter();
        },

        _startTimeCounter: function () {
            var self = this;
            clearTimeout(this.timer);

            if (this.record.data.is_user_working) {
                this.timer = setTimeout(function () {
                    self.duration += 1000;
                    self._startTimeCounter();
                    self._rpc({
                        model: 'project.task',  // Replace with your model name
                        method: 'write',
                        args: [[self.res_id], { duration: self.duration / 3600000 }],  // Convert milliseconds to hours
                    }).then(function () {
                        console.log("Duration updated successfully");
                    });

                }, 1000);
            } else {
                clearTimeout(this.timer);
            }

            var duration = moment.duration(this.duration, 'milliseconds');

            if (duration.asMilliseconds() < 0) {
                duration = moment.duration(0, 'milliseconds');
            }

            var years = Math.floor(duration.asYears());
            duration.subtract(years, 'years');

            var months = Math.floor(duration.asMonths());
            duration.subtract(months, 'months');

            var days = Math.floor(duration.asDays());
            duration.subtract(days, 'days');

            var hours = duration.hours();
            var minutes = duration.minutes();
            var seconds = duration.seconds();

            //var formattedDuration = `${years}y ${months}m ${days}d ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            var formattedTime =
                (years > 0 ? years + "A " : "") +
                (months > 0 ? months + "M " : "") +
                (days > 0 ? days + "J " : "") +
                hours.toString().padStart(2, '0') + ":" +
                minutes.toString().padStart(2, '0') + ":" +
                seconds.toString().padStart(2, '0');

//            var formattedTime =
//                (years > 0 ? years + (years > 1 ? "Années " : "Année ") : "") +
//                (months > 0 ? months + (months > 1 ? "Mois " : "Mois ") : "") +
//                (days > 0 ? days + (days > 1 ? "Jours " : "Jour ") : "") +
//                hours.toString().padStart(2, '0') + ":" +
//                minutes.toString().padStart(2, '0') + ":" +
//                seconds.toString().padStart(2, '0');

            this.$el.html($('<span class="inactivity-time">' + formattedTime + '</span>'));
        },

        /*_startIdleCounter: function () {
            var self = this;
            clearTimeout(this.idleTimer);

            if (!this.record.data.is_user_working) {
                this.idleTimer = setTimeout(function () {
                    self.idleDuration += 1000;
                    self._startIdleCounter();
                }, 1000);
            } else {
                clearTimeout(this.idleTimer);
            }

            var idleDuration = moment.duration(this.idleDuration, 'milliseconds');
            var idleYears = Math.floor(idleDuration.asYears());
            idleDuration.subtract(idleYears, 'years');

            var idleMonths = Math.floor(idleDuration.asMonths());
            idleDuration.subtract(idleMonths, 'months');

            var idleDays = Math.floor(idleDuration.asDays());
            idleDuration.subtract(idleDays, 'days');

            var idleHours = idleDuration.hours();
            var idleMinutes = idleDuration.minutes();
            var idleSeconds = idleDuration.seconds();

            var formattedIdleTime =
                (idleYears > 0 ? idleYears + (idleYears > 1 ? "A " : "A ") : "") +
                (idleMonths > 0 ? idleMonths + (idleMonths > 1 ? "M " : "M ") : "") +
                (idleDays > 0 ? idleDays + (idleDays > 1 ? "J " : "J ") : "") +
                idleHours.toString().padStart(2, '0') + ":" +
                idleMinutes.toString().padStart(2, '0') + ":" +
                idleSeconds.toString().padStart(2, '0') ;

            // Display idle time in a separate span
            //this.$el.find(".inactivity-time").append(formattedIdleTime);
        },*/

    });

    field_registry.add('intervention_duration', TimeCounter);
});
