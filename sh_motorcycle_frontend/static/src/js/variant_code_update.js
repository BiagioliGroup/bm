odoo.define("sh_motorcycle_frontend.variant_code_update", function (require) {
  "use strict";

  const publicWidget = require("web.public.widget");

  publicWidget.registry.VariantCodeUpdater = publicWidget.Widget.extend({
    selector: ".js_sale",

    events: {
      "change .product_id": "_onVariantChange",
    },

    _onVariantChange: function () {
      const $defaultCodeDiv = $("#variant_default_code");
      const productId = $(".product_id").val();

      if (!productId) return;

      this._rpc({
        model: "product.product",
        method: "read",
        args: [[parseInt(productId)], ["default_code"]],
      }).then(function (result) {
        if (result && result[0] && result[0].default_code) {
          $defaultCodeDiv.html(
            `<strong>Código:</strong> ${result[0].default_code}`
          );
        }
      });
    },
  });
});
