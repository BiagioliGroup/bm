odoo.define("sh_motorcycle_frontend.variant_code_update", function (require) {
  "use strict";

  console.log("[variant_code_update] Script loaded");

  const publicWidget = require("web.public.widget");

  publicWidget.registry.VariantCodeUpdater = publicWidget.Widget.extend({
    selector: ".js_sale",

    events: {
      "change .product_id": "_onVariantChange",
    },

    start: function () {
      console.log("[variant_code_update] Widget iniciado");
      return this._super.apply(this, arguments);
    },

    _onVariantChange: function (ev) {
      console.log("[variant_code_update] Detected change on .product_id");

      const $defaultCodeDiv = $("#variant_default_code");
      const productId = $(".product_id").val();

      console.log("[variant_code_update] Selected productId:", productId);

      if (!productId) {
        console.warn("[variant_code_update] No product_id found");
        return;
      }

      this._rpc({
        model: "product.product",
        method: "read",
        args: [[parseInt(productId)], ["default_code"]],
      })
        .then(function (result) {
          console.log("[variant_code_update] RPC result:", result);

          if (result && result[0] && result[0].default_code) {
            $defaultCodeDiv.html(
              `<strong>Código:</strong> ${result[0].default_code}`
            );
            console.log("[variant_code_update] Código actualizado");
          } else {
            $defaultCodeDiv.html("");
            console.warn(
              "[variant_code_update] No default_code found in result"
            );
          }
        })
        .catch(function (error) {
          console.error("[variant_code_update] RPC error:", error);
        });
    },
  });
});
