odoo.define("sh_motorcycle_frontend.variant_code_update", function (require) {
  "use strict";

  console.log("[variant_code_update] Script loaded");

  $(document).ready(function () {
    console.log("[variant_code_update] Document ready");

    $("body").on("change", ".product_id", function () {
      const productId = $(this).val();
      console.log("[variant_code_update] product_id changed:", productId);

      if (productId) {
        const $defaultCodeDiv = $("#variant_default_code");

        odoo
          .rpc({
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
            } else {
              $defaultCodeDiv.html("");
            }
          })
          .catch(function (error) {
            console.error("[variant_code_update] RPC error:", error);
          });
      }
    });
  });
});
