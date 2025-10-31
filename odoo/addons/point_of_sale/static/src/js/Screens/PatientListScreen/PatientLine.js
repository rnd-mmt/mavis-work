odoo.define('point_of_sale.PatientLine', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class PatientLine extends PosComponent {
        get highlight() {
            return this.props.partner !== this.props.selectedPatient ? '' : 'highlight';
        }
    }
    PatientLine.template = 'PatientLine';

    Registries.Component.add(PatientLine);

    return PatientLine;
});
