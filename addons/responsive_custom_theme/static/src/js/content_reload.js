odoo.define('responsive_custom_theme.content_reloader', function(require) {
    "use strict";
    var wr_form_controller = require('web.FormController');
    var wr_list_controller = require('web.ListController');
    var wr_graph_controller = require('web.GraphController');
    var wr_calendar_controller = require('web.CalendarController');
    var wr_kanban_controller = require('web.KanbanController');
    var wr_pivot_controller = require('web.PivotController');
    var session = require("web.session");

    /* Form view */
    wr_form_controller.include({
        events: _.extend({}, wr_form_controller.prototype.events, {
            "click button.reload_form_view": "_WrFormReloadView",
        }),
        _WrFormReloadView: function() { this.reload(); },
    });

    /* List view */
    wr_list_controller.include({
        events: _.extend({}, wr_list_controller.prototype.events, {
            "click .reload_list_view": "_WrReloadListView",
        }),
         _WrReloadListView: function() { this.reload(); },
    });

    /* Graph view */
    wr_graph_controller.include({
        events: _.extend({}, wr_graph_controller.prototype.events, {
            "click .reload_list_view": "_WrReloadGraphView",
        }),
        _WrReloadGraphView: function() { this.reload(); },
    });

    /* Calendar view */
    wr_calendar_controller.include({
        events: _.extend({}, wr_calendar_controller.prototype.events, {
            "click button.reload_view": "_WrReloadCalendarView",
        }),
        _WrReloadCalendarView: function() { this.reload();},
    });

    /* kanban view */
     wr_kanban_controller.include({
        events: _.extend({}, wr_kanban_controller.prototype.events, {
            "click button.reload_view": "_WrReloadKanbanView",
        }),
     _WrReloadKanbanView: function() { this.reload();},
    });

    /* Pivot view */
    wr_pivot_controller.include({
        events: _.extend({}, wr_pivot_controller.prototype.events, {
            "click button.reload_view": "_WrReloadPivotView",
        }),
        _WrReloadPivotView: function() { this.reload();},
    });

});