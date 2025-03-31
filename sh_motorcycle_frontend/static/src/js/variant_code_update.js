odoo.define("sh_motorcycle_frontend.variant_code_update", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");
  var rpc = require("web.rpc");

  console.log("[variant_code_update] Script loaded");

  publicWidget.registry.VariantCodeUpdater = publicWidget.Widget.extend({
    selector: ".oe_website_sale",
    start: function () {
      console.log("[variant_code_update] Widget start");

      this._updateDefaultCode();
      this._bindEvents();
      return this._super.apply(this, arguments);
    },
    _bindEvents: function () {
      var self = this;
      this.$el.on("change", 'input[name="product_id"]', function () {
        self._updateDefaultCode();
      });
    },
    _updateDefaultCode: function () {
      var self = this;
      var $productInput = this.$('input[name="product_id"]');
      var $defaultCodeContainer = $("#variant_default_code");

      var productId = parseInt($productInput.val());
      if (!productId || !$defaultCodeContainer.length) {
        return;
      }

      rpc
        .query({
          model: "product.product",
          method: "read",
          args: [[productId], ["default_code"]],
        })
        .then(function (result) {
          if (result.length && result[0].default_code) {
            $defaultCodeContainer.html(
              `<strong>Código:</strong> ${result[0].default_code}`
            );
            console.log(
              "[variant_code_update] Updated code:",
              result[0].default_code
            );
          } else {
            $defaultCodeContainer.empty();
          }
        })
        .catch(function (error) {
          console.error("[variant_code_update] RPC error:", error);
        });
    },
  });
});
