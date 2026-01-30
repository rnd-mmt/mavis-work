odoo.define('maintenance_contract.donut_chart_widget', function (require) {
    "use strict";

    const AbstractField = require('web.AbstractField');
    const fieldRegistry = require('web.field_registry');

    const DonutChartWidget = AbstractField.extend({
        template: 'maintenance_contract.DonutChartWidget',
        _render: function () {
            const value = parseFloat(this.value) || 0;
            this.$el.html(`
                <div class="percentage" style="margin-bottom: 8px;">
                    ${value.toFixed(2)} %
                </div>
                <div class="chart">
                    <div class="donut-chart" style="--percentage: ${value};">
                        <div class="donut-percentage"></div>
                    </div>
                </div>
            `);
        }
    });

    fieldRegistry.add('donut_chart_widget', DonutChartWidget);
});
