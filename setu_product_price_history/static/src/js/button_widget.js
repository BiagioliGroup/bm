/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

// Create widget "smartButtonWidget" , #Task:1394, #Jatin.
export class smartButtonWidget extends Component {
    setup() {
        this.actionService = useService("action");
    }

    onClick() {
        var self = this;
        var method = "";
        rpc('/web/dataset/call_kw', {model: 'sale.order.line',
                    method: (self.props.name == "product_sale_id_reference") ? "show_product_sale_lines" : "show_product_purchase_lines",
                    args: [0,this.props.record.data['product_id'][0]],
                    kwargs: {},
                }).then(function(action) {
                debugger
                     self.actionService.doAction(action);
                });
    }
}

smartButtonWidget.template = "setu_product_price_history.buttonWidget";

export const SmartButtonWidget = {
    component: smartButtonWidget,
    supportedTypes: ["integer"],
};

registry.category("fields").add("smartButtonWidget", SmartButtonWidget);
