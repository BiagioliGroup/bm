/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

publicWidget.registry.sh_motorcycle_shop_search = publicWidget.Widget.extend({
  selector: "#wrap",
  events: {
    "change #id_sh_motorcycle_type_select": "_onChangeTypeGetMake",
    "change #id_sh_motorcycle_make_select": "_onChangeMakeGetYear",
    "change #id_sh_motorcycle_year_select": "_onChangeYearGetModel",
    "change #id_sh_motorcycle_model_select": "_onChangeModel",
    "click #id_sh_motorcycle_select_diff_bike_btn": "_onClickSelectDiffVehicle",
    "click #id_sh_motorcycle_search_diff_bike_close":
      "_onClickSelectDiffVehicleClose",
    "click #id_sh_motorcycle_save_bike_to_garage_btn":
      "_onClickSaveBikeToGarage",
    "click .js_cls_remove_vehicle_button": "_onClickRemoveVehicle",
  },

  start: function () {
    var self = this;
    self.loadTypeList();
    self.diable_select_options();

    var result = self.getQueryString();
    if (result["type"] && result["make"] && result["year"] && result["model"]) {
      rpc("/sh_motorcycle/is_bike_already_in_garage", {
        type_id: result["type"],
        make_id: result["make"],
        year: result["year"],
        model_id: result["model"],
      }).then(function (rec) {
        if (rec.is_bike_already_in_garage) {
          $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
        } else {
          $("#id_sh_motorcycle_save_bike_to_garage_btn").show();
        }
      });
    } else {
      $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
    }

    $("#id_sh_motorcycle_select_saved_bike_div > a").remove();
    rpc("/sh_motorcycle/get_saved_bike").then(function (data) {
      jQuery.each(data, function (key, value) {
        $("#id_sh_motorcycle_select_saved_bike_div").append(
          '<a class="dropdown-item" href="' +
            value.moto_url +
            '">' +
            value.name +
            "</a>"
        );
      });
    });
  },

  loadTypeList: function () {
    $("#id_sh_motorcycle_type_select > option").not(":first").remove();
    rpc("/sh_motorcycle/get_type_list").then((data) => {
      jQuery.each(data, (key, value) => {
        $("#id_sh_motorcycle_type_select").append(
          '<option value="' + value.id + '">' + value.name + "</option>"
        );
      });
    });
  },

  _onChangeTypeGetMake: function (e) {
    e.preventDefault();
    $("#id_sh_motorcycle_make_select > option").not(":first").remove();
    $("#id_sh_motorcycle_year_select > option").not(":first").remove();
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();
    rpc("/sh_motorcycle/get_make_list", {
      type_id:
        $("#id_sh_motorcycle_type_select").val() ||
        $('select[name="type"]').val(),
    }).then((data) => {
      jQuery.each(data, (key, value) => {
        $("#id_sh_motorcycle_make_select").append(
          '<option value="' + value.id + '">' + value.name + "</option>"
        );
      });
      this.diable_select_options();
    });
  },

  _onChangeMakeGetYear: function (e) {
    e.preventDefault();
    $("#id_sh_motorcycle_year_select > option").not(":first").remove();
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();
    rpc("/sh_motorcycle/get_year_list", {
      type_id:
        $("#id_sh_motorcycle_type_select").val() ||
        $('select[name="type"]').val(),
      make_id:
        $("#id_sh_motorcycle_make_select").val() ||
        $('select[name="make"]').val(),
    }).then((data) => {
      data.forEach((year) => {
        $("#id_sh_motorcycle_year_select").append(
          `<option value="${year}">${year}</option>`
        );
      });
      this.diable_select_options();
    });
  },

  _onChangeYearGetModel: function (e) {
    e.preventDefault();
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();
    $("#no_model_message").remove();
    rpc("/sh_motorcycle/get_model_list", {
      type_id:
        $("#id_sh_motorcycle_type_select").val() ||
        $('select[name="type"]').val(),
      make_id:
        $("#id_sh_motorcycle_make_select").val() ||
        $('select[name="make"]').val(),
      year:
        $("#id_sh_motorcycle_year_select").val() ||
        $('select[name="year"]').val(),
    }).then((data) => {
      if (data.length === 0) {
        $("#id_sh_motorcycle_model_select").after(
          '<small id="no_model_message" class="text-danger d-block mt-1">No hay modelos disponibles para este año.</small>'
        );
        $("#id_sh_motorcycle_model_select").prop("disabled", true);
      } else {
        data.forEach((d) => {
          $("#id_sh_motorcycle_model_select").append(
            `<option value="${d.id}">${d.name}</option>`
          );
        });
        $("#id_sh_motorcycle_model_select").prop("disabled", false);
      }
      this.diable_select_options();
    });
  },

  _onChangeModel: function (e) {
    e.preventDefault();
    this.diable_select_options();
  },

  _onClickSelectDiffVehicle: function () {
    var self = this;

    $("#id_sh_motorcycle_search_diff_bike_div").toggle();
    $("#id_sh_motorcycle_select_diff_bike_btn").toggle();
    self.save_bike_to_garage_btn_old_style = $(
      "#id_sh_motorcycle_save_bike_to_garage_btn"
    ).css("display");
    $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();

    $("#id_sh_motorcycle_type_select").val("");
    $("#id_sh_motorcycle_make_select")
      .html('<option value="">Marca</option>')
      .prop("disabled", true);
    $("#id_sh_motorcycle_year_select")
      .html('<option value="">Año</option>')
      .prop("disabled", true);
    $("#id_sh_motorcycle_model_select")
      .html('<option value="">Modelo</option>')
      .prop("disabled", true);

    $('select[name="type"]').val("").prop("disabled", false);
    $('select[name="make"]')
      .html('<option value="">Marca</option>')
      .prop("disabled", true);
    $('select[name="year"]')
      .html('<option value="">Año</option>')
      .prop("disabled", true);
    $('select[name="model"]')
      .html('<option value="">Modelo</option>')
      .prop("disabled", true);

    $("#id_sh_motorcycle_go_submit_button").prop("disabled", true);
    $("#no_model_message").remove();

    self.loadTypeList();

    // Reenganchar eventos
    $("#id_sh_motorcycle_type_select")
      .off("change")
      .on("change", self._onChangeTypeGetMake.bind(self));
    $('select[name="type"]')
      .off("change")
      .on("change", self._onChangeTypeGetMake.bind(self));

    self.diable_select_options();
  },

  _onClickSelectDiffVehicleClose: function (ev) {
    var self = this;
    $("#id_sh_motorcycle_search_diff_bike_div").toggle();
    $("#id_sh_motorcycle_select_diff_bike_btn").toggle();
    $("#id_sh_motorcycle_save_bike_to_garage_btn").css(
      "display",
      self.save_bike_to_garage_btn_old_style
    );
  },

  getQueryString: function () {
    var result = {};
    if (!window.location.search.length) return result;
    var qs = window.location.search.slice(1);
    var parts = qs.split("&");
    for (var i = 0, len = parts.length; i < len; i++) {
      var tokens = parts[i].split("=");
      result[tokens[0]] = decodeURIComponent(tokens[1]);
    }
    return result;
  },

  diable_select_options: function () {
    var typeSelected = $(
      "#id_sh_motorcycle_type_select > option:selected"
    ).val();
    if (typeSelected) {
      $("#id_sh_motorcycle_make_select").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_make_select").prop("disabled", true);
    }

    var makeSelected = $(
      "#id_sh_motorcycle_make_select > option:selected"
    ).val();
    if (makeSelected) {
      $("#id_sh_motorcycle_year_select").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_year_select").prop("disabled", true);
    }

    var yearSelected = $(
      "#id_sh_motorcycle_year_select > option:selected"
    ).val();
    if (yearSelected) {
      $("#id_sh_motorcycle_model_select").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_model_select").prop("disabled", true);
    }

    var modelSelected = $(
      "#id_sh_motorcycle_model_select > option:selected"
    ).val();
    if (modelSelected) {
      $("#id_sh_motorcycle_go_submit_button").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_go_submit_button").prop("disabled", true);
    }
  },

  _onClickSaveBikeToGarage: function (ev) {
    var self = this;
    var result = self.getQueryString();

    rpc("/sh_motorcycle/add_bike_to_garage", {
      type_id: result["type"],
      make_id: result["make"],
      model_id: result["model"],
      year: result["year"],
    }).then(function (rec) {
      $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
      var query = $.param(result);
      window.location.href = "/shop?" + query;
    });
  },

  _onClickRemoveVehicle: async function (ev) {
    var motorcycle_id = $(ev.currentTarget).data("motorcycle_id");
    this.call("dialog", "add", ConfirmationDialog, {
      body: _t("Estas seguro de eliminar este vehiculo?"),
      confirm: async () => {
        window.location.href = "/my/garage/remove_bike?id=" + motorcycle_id;
      },
      cancleLabel: _t("Cancel"),
      confirmLabel: _t("Yes"),
      cancel: () => {},
    });
  },
});
