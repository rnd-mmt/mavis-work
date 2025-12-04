odoo.define('point_of_sale.ActionpadWidget', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    /**
     * @props client
     * @emits click-customer
     * @emits click-pay
     */
    class ActionpadWidget extends PosComponent {
        get isPatientLongName() {
            return this.patient && this.patient.name.length > 10;
        }
        // get patient() {
        //     return this.props.patient;
        // }

        // get client() {
        //     return this.props.client;
        // }
        get patient() {
            const order = this.env.pos.get_order();
            return order ? order.get_patient() : null;
        }

        get client() {
            const order = this.env.pos.get_order();
            return order ? order.get_client() : null;
        }


        get isLongName() {
            return this.client && this.client.name.length > 10;
        }
    }
    ActionpadWidget.template = 'ActionpadWidget';

    Registries.Component.add(ActionpadWidget);

    return ActionpadWidget;
});
