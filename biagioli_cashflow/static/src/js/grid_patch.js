/** biagioli_cashflow/static/src/js/grid_patch.js */
odoo.define("biagioli_cashflow.grid_patch", function (require) {
  "use strict";
  const GridRenderer = require("web.GridRenderer");
  const { patch } = require("web.utils");

  patch(GridRenderer.prototype, "biagioli_cashflow.GridRenderer", {
    _renderRow(row, node, { extra }) {
      const $tr = this._super(...arguments);
      if (row.values.type && !row.values.partner_id) {
        const type = row.values.type[0];
        $tr.addClass(
          type === "ingreso"
            ? "o_cashflow_type_ingreso"
            : "o_cashflow_type_egreso"
        );
      }
      return $tr;
    },
  });
});
