/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

publicWidget.registry.sh_motorcycle_shop_search = publicWidget.Widget.extend({
  selector: "#wrap",

  events: {
    "change #id_sh_motorcycle_type_select": "_onChangeType",
    "change #id_sh_motorcycle_make_select": "_onChangeMake",
    "change #id_sh_motorcycle_year_select": "_onChangeYear",
    "change #id_sh_motorcycle_model_select": "_onChangeModel",

    "change select[name='type']": "_onChangeType",
    "change select[name='make']": "_onChangeMake",
    "change select[name='year']": "_onChangeYear",
    "change select[name='model']": "_onChangeModel",

    "click #id_sh_motorcycle_select_diff_bike_btn": "_onClickSelectDiffVehicle",
    "click #id_sh_motorcycle_search_diff_bike_close":
      "_onClickSelectDiffVehicleClose",
    "click #id_sh_motorcycle_save_bike_to_garage_btn":
      "_onClickSaveBikeToGarage",
    "click .js_cls_remove_vehicle_button": "_onClickRemoveVehicle",
  },

  start: function () {
    this._super(...arguments);
    this._initializeSelectors();
    this._loadSavedBikes();
    this._checkSavedButton();
  },

  /*** CARGAS Y RESETEOS ***/

  _initializeSelectors: function () {
    this._resetSelectors();
    this.loadTypeList();
  },

  _resetSelectors: function () {
    this.renderSelect($("#id_sh_motorcycle_type_select"), [], "Tipo");
    this.renderSelect($("select[name='type']"), [], "Tipo");
    this.renderSelect($("#id_sh_motorcycle_make_select"), [], "Marca", true);
    this.renderSelect($("select[name='make']"), [], "Marca", true);
    this.renderSelect($("#id_sh_motorcycle_year_select"), [], "Año", true);
    this.renderSelect($("select[name='year']"), [], "Año", true);
    this.renderSelect($("#id_sh_motorcycle_model_select"), [], "Modelo", true);
    this.renderSelect($("select[name='model']"), [], "Modelo", true);
    $("#id_sh_motorcycle_go_submit_button").prop("disabled", true);
  },

  renderSelect: function ($select, items, placeholder, disabled = false) {
    $select.empty();
    $select.append(`<option value="">${placeholder}</option>`);
    const unique = new Set();
    items.forEach((item) => {
      const value = item.id || item;
      const text = item.name || item;
      if (!unique.has(value)) {
        $select.append(`<option value="${value}">${text}</option>`);
        unique.add(value);
      }
    });
    $select.prop("disabled", disabled);
  },

  /*** CARGA LISTAS DE OPCIONES ***/

  loadTypeList: function () {
    rpc("/sh_motorcycle/get_type_list").then((data) => {
      this.renderSelect($("#id_sh_motorcycle_type_select"), data, "Tipo");
      this.renderSelect($("select[name='type']"), data, "Tipo");
    });
  },

  loadMakeList: function (type_id) {
    if (!type_id) return;
    rpc("/sh_motorcycle/get_make_list", { type_id }).then((data) => {
      this.renderSelect($("#id_sh_motorcycle_make_select"), data, "Marca");
      this.renderSelect($("select[name='make']"), data, "Marca");
    });
  },

  loadYearList: function (type_id, make_id) {
    if (!type_id || !make_id) return;
    rpc("/sh_motorcycle/get_year_list", { type_id, make_id }).then((data) => {
      this.renderSelect($("#id_sh_motorcycle_year_select"), data, "Año");
      this.renderSelect($("select[name='year']"), data, "Año");
    });
  },

  loadModelList: function (type_id, make_id, year) {
    if (!type_id || !make_id || !year) return;
    rpc("/sh_motorcycle/get_model_list", { type_id, make_id, year }).then(
      (data) => {
        this.renderSelect($("#id_sh_motorcycle_model_select"), data, "Modelo");
        this.renderSelect($("select[name='model']"), data, "Modelo");
      }
    );
  },

  /*** EVENTOS ***/

  _onChangeType: function () {
    const type_id =
      $("#id_sh_motorcycle_type_select").val() ||
      $("select[name='type']").val();
    this.loadMakeList(type_id);
    this.renderSelect($("#id_sh_motorcycle_year_select"), [], "Año", true);
    this.renderSelect($("select[name='year']"), [], "Año", true);
    this.renderSelect($("#id_sh_motorcycle_model_select"), [], "Modelo", true);
    this.renderSelect($("select[name='model']"), [], "Modelo", true);
  },

  _onChangeMake: function () {
    const type_id =
      $("#id_sh_motorcycle_type_select").val() ||
      $("select[name='type']").val();
    const make_id =
      $("#id_sh_motorcycle_make_select").val() ||
      $("select[name='make']").val();
    this.loadYearList(type_id, make_id);
    this.renderSelect($("#id_sh_motorcycle_model_select"), [], "Modelo", true);
    this.renderSelect($("select[name='model']"), [], "Modelo", true);
  },

  _onChangeYear: function () {
    const type_id =
      $("#id_sh_motorcycle_type_select").val() ||
      $("select[name='type']").val();
    const make_id =
      $("#id_sh_motorcycle_make_select").val() ||
      $("select[name='make']").val();
    const year =
      $("#id_sh_motorcycle_year_select").val() ||
      $("select[name='year']").val();
    this.loadModelList(type_id, make_id, year);
  },

  _onChangeModel: function () {
    const model_id =
      $("#id_sh_motorcycle_model_select").val() ||
      $("select[name='model']").val();
    $("#id_sh_motorcycle_go_submit_button").prop("disabled", !model_id);
  },

  _onClickSelectDiffVehicle: function () {
    this._resetSelectors();
    this.loadTypeList();
    $("#id_sh_motorcycle_search_diff_bike_div").toggle();
    $("#id_sh_motorcycle_select_diff_bike_btn").toggle();
    $(".motorcycle_heading_section").fadeOut();
  },

  _onClickSelectDiffVehicleClose: function () {
    $("#id_sh_motorcycle_search_diff_bike_div").toggle();
    $("#id_sh_motorcycle_select_diff_bike_btn").toggle();
  },

  _onClickSaveBikeToGarage: function () {
    const params = this.getQueryString();
    rpc("/sh_motorcycle/add_bike_to_garage", params).then(() => {
      $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
      window.location.href = "/shop?" + $.param(params);
    });
  },

  _onClickRemoveVehicle: async function (ev) {
    const motorcycle_id = $(ev.currentTarget).data("motorcycle_id");
    this.call("dialog", "add", ConfirmationDialog, {
      body: _t("Estas seguro de eliminar este vehiculo?"),
      confirm: async () => {
        window.location.href = "/my/garage/remove_bike?id=" + motorcycle_id;
      },
      cancelLabel: _t("Cancelar"),
      confirmLabel: _t("Confirmar"),
    });
  },

  /*** UTILIDADES ***/

  getQueryString: function () {
    const result = {};
    window.location.search
      .slice(1)
      .split("&")
      .forEach((item) => {
        const [key, value] = item.split("=");
        result[key] = decodeURIComponent(value);
      });
    return result;
  },

  _loadSavedBikes: function () {
    $("#id_sh_motorcycle_select_saved_bike_div > a").remove();
    rpc("/sh_motorcycle/get_saved_bike").then((data) => {
      data.forEach((bike) => {
        $("#id_sh_motorcycle_select_saved_bike_div").append(
          `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`
        );
      });
    });
  },

  _checkSavedButton: function () {
    const params = this.getQueryString();
    if (params.type && params.make && params.year && params.model) {
      rpc("/sh_motorcycle/is_bike_already_in_garage", params).then((rec) => {
        if (rec.is_bike_already_in_garage) {
          $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
        } else {
          $("#id_sh_motorcycle_save_bike_to_garage_btn").show();
        }
      });
    } else {
      $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
    }
  },
});
