/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.js_editor_sh_motorcycle_frontend_tmpl_1 = options.Class.extend(
  {
    //for select category
    selectClass: function (previewMode, value, $li) {
      this._super.apply(this, arguments);

      if (value && value.length && value != "") {
        var val_2 = value;
        var category_id = 0;
        category_id = val_2.replace("sh_moto_categ_", "");
        category_id = parseInt(category_id);
        this.$target.find('input[name="category"]').val(category_id);
      } else if (value && value.length && value == "") {
        this.$target.find('input[name="category"]').val("");
      }
    },
  }
);
