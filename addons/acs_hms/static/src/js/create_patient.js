odoo.define('acs_hms.control_panel_inherit', function (require) {

    "use strict" ;
    var t_form_controller = require('web.FormController') ;
    var t_list_controller = require('web.ListController') ;
    var t_kanban_controller = require('web.KanbanController') ;
    var ControlPanel = require('web.ControlPanel') ;

    var WebClient = require('web.WebClient') ;
    var core = require('web.core') ;
    var _t = core._t ;

    /* MANAGE VISIBILITY OF PATIENT CREATION BUTTON */
    jQuery(document).ready(function($) {

        function isPatientModel() {
           var currentUrl = window.location.href;
           return currentUrl.includes('&model=hms.patient&');
       }

        function overrideCreateButton() {
           MutationObserver = window.MutationObserver || window.WebKitMutationObserver;
           var observer = new MutationObserver(function(mutations, observer) {
               if ( isPatientModel()) {
                   var createBtn = $('button.o-kanban-button-new').length ? $('button.o-kanban-button-new') :
                       $('.o_form_button_create').length ? $('.o_form_button_create') :
                       $('.o_list_button_add').length ? $('.o_list_button_add') : null;
                   var createPatientBtn = $('.patient_creation_checking');
                   $(createPatientBtn).removeClass('o_hidden');
                   $(createBtn).replaceWith(createPatientBtn);
               }
           });
           observer.observe(document, { subtree: true, attributes: true });
       }

       ( function() {
            overrideCreateButton();
       })();

       $(window).on('hashchange load',  function() {
            overrideCreateButton();
       });

       document.addEventListener('DOMContentLoaded',  function() {
            overrideCreateButton();
       });
   });


    /* Form View */
    t_form_controller.include({
        events: _.extend({}, t_form_controller.prototype.events, {
            "click .patient_creation_checking": "_tShowPatientCreationWizard",
        }),
        _tShowPatientCreationWizard: function() {
            this.do_action('acs_hms.action_patient_creation_wizard') ;
        },
    });

    /* List View */
    t_list_controller.include({
        events: _.extend({}, t_list_controller.prototype.events, {
            "click .patient_creation_checking": "_tShowPatientCreationWizard",
        }),
         _tShowPatientCreationWizard: function() {
            this.do_action('acs_hms.action_patient_creation_wizard') ;
         },
    });

    /* Kanban View */
     t_kanban_controller.include({
        events: _.extend({}, t_kanban_controller.prototype.events, {
            "click .patient_creation_checking": "_tShowPatientCreationWizard",
        }),
        _tShowPatientCreationWizard: function() {
            this.do_action('acs_hms.action_patient_creation_wizard') ;
        },
    });

});
