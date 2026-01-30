odoo.define('health_service.cp_button_create_inherit', function (require) {

    "use strict" ;
    var t_form_controller = require('web.FormController') ;
    var t_list_controller = require('web.ListController') ;
    var t_kanban_controller = require('web.KanbanController') ;
    var WebClient = require('web.WebClient') ;
    var FieldMany2Many = require('web.relational_fields').FieldMany2Many;
    var ActionManager = require('web.ActionManager');
    var core = require('web.core') ;
    var KanbanRecord = require('web.KanbanRecord');
    var _t = core._t ;

    /* MANAGE VISIBILITY OF PATIENT CREATION BUTTON */
    function is_service_sante_model() {
        var currentUrl = window.location.href ;
        if ( currentUrl.includes('&model=acs.health_service&') ) {
            return true;
        } else {
            return false;
        }
    }
    // Override create button if current model is 'hms.patient'
    function override_create_button() {
        MutationObserver = window.MutationObserver || window.WebKitMutationObserver;
        var observer = new MutationObserver(function(mutations, observer) {
            if ( is_service_sante_model() ) {
                var createBtn = $('.o_list_button_add').length ? $('.o_list_button_add') :
                    $('.o-kanban-button-new').length ? $('.o-kanban-button-new') :
                    $('.o_form_button_create').length ? $('.o_form_button_create') : null;
                var createHsBtn = $('.health_service_creation');

                $(createHsBtn).removeClass('o_hidden');
                $(createBtn).replaceWith(createHsBtn);
            }
        });
        observer.observe(document, { subtree: true, attributes: true });
    }

    window.addEventListener('load', function() {
        override_create_button();
    });

    jQuery(document).ready(function($){

        setTimeout( function(){
            override_create_button();
        } , 500);

        // On Document Ready
        override_create_button();
        if ( $('.o_facet_values').length ) {
            override_create_button();
        }

        // On Hash Change
        $(window).on('hashchange', function (e) {
            override_create_button();
        }).trigger('hashchange load');

        // On Document Content Loaded
        document.addEventListener('DOMContentLoaded', function() {
            override_create_button();
        });

        window.addEventListener('load', function() {
            override_create_button();
        });

    });

    /* Form View */
    t_form_controller.include({
        events: _.extend({}, t_form_controller.prototype.events, {
            "click .health_service_creation": "_tShowHeathServiceCreationWizard",
        }),
        _tShowHeathServiceCreationWizard: function() {
            this.do_action('health_service.action_health_service_creation_wizard') ;
        },
    });

    /* List View */
    t_list_controller.include({
        events: _.extend({}, t_list_controller.prototype.events, {
            "click .health_service_creation": "_tShowHeathServiceCreationWizard",
        }),
         _tShowHeathServiceCreationWizard: function() {
            this.do_action('health_service.action_health_service_creation_wizard') ;
         },
    });

    /* Kanban View */
     t_kanban_controller.include({
        events: _.extend({}, t_kanban_controller.prototype.events, {
            "click .health_service_creation": "_tShowHeathServiceCreationWizard",
        }),
        _tShowHeathServiceCreationWizard: function() {
            this.do_action('health_service.action_health_service_creation_wizard') ;
        },
    });


    /* CREATE HEALTH SERVICE FROM SELECTED ITEM FOR EACH ITEM ON KANBAN VIEW */
    KanbanRecord.include({
        events: _.extend({}, KanbanRecord.prototype.events, {
            'click .oe_kanban_action_button': '_onCreateRecord',
        }),

        _onCreateRecord: function (event) {
            event.preventDefault();
            var self = this;
            var $kanbanRecord = $(event.currentTarget).closest('.oe_kanban_global_click');
            var patientIdText = $kanbanRecord.find('span.patient-id span').text().trim();
            patientIdText = patientIdText.replace(/\D/g, '');
            var patientId = Number(patientIdText);
            console.log('id_pation:', patientId);
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'acs.health_service',
                views: [[false, 'form']],
                target: 'current',
                context: {
                    'default_patient_id': patientId,
                },
            });
        },
    });

});
