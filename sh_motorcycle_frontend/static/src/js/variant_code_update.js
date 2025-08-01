// odoo.define("sh_motorcycle_frontend.variant_code_update", function (require) {
//   "use strict";
//   var publicWidget, rpc;
//   try {
//     // Intento cargar las dependencias sólo si existen
//     publicWidget = require("web.public.widget");
//     rpc          = require("web.rpc");
//   } catch (e) {
//     // Si no están, salimos sin romper nada
//     console.warn("variant_code_update: dependencias faltantes, módulo saltado", e);
//     return;
//   }

//   console.log("[variant_code_update] Script loaded");

//   publicWidget.registry.VariantCodeUpdater = publicWidget.Widget.extend({
//     selector: ".oe_website_sale",      // sólo donde exista este contenedor
//     start: function () {
//       console.log("[variant_code_update] Widget start");
//       this._updateDefaultCode();
//       this._bindEvents();
//       return this._super.apply(this, arguments);
//     },
//     _bindEvents: function () {
//       var self = this;
//       this.$el.on("change", 'input[name="product_id"]', function () {
//         self._updateDefaultCode();
//       });
//     },
//     _updateDefaultCode: function () {
//       var $input   = this.$('input[name="product_id"]'),
//           $cont    = $("#variant_default_code"),
//           productId = parseInt($input.val());
//       if (!productId || !$cont.length) {
//         return;
//       }
//       rpc.query({
//         model:  "product.product",
//         method: "read",
//         args:   [[productId], ["default_code"]],
//       }).then(function (res) {
//         if (res[0] && res[0].default_code) {
//           $cont.html(`<strong>Código:</strong> ${res[0].default_code}`);
//           console.log("[variant_code_update] Updated code:", res[0].default_code);
//         } else {
//           $cont.empty();
//         }
//       }).catch(function (err) {
//         console.error("[variant_code_update] RPC error:", err);
//       });
//     },
//   });
// });
