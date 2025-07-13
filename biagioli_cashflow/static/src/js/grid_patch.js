/** biagioli_cashflow/static/src/js/grid_patch.js */
odoo.define("biagioli_cashflow.grid_patch", function (require) {
  "use strict";
  const GridRenderer = require("web.GridRenderer");
  const { patch } = require("web.utils");

  patch(GridRenderer.prototype, "biagioli_cashflow.GridRenderer", {
    _renderRow(row, node, { extra }) {
      const $tr = this._super(...arguments);
      // row.values holds grouping values in order
      const isTypeGroup =
        row.values.type !== undefined && row.values.name === undefined;
      if (isTypeGroup) {
        if (row.values.type[0] === "ingreso") {
          $tr.addClass("o_cashflow_type_ingreso");
        } else {
          $tr.addClass("o_cashflow_type_egreso");
        }
      }
      return $tr;
    },
  });
});
