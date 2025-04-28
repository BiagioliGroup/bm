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
    this._fillSelect("#id_sh_motorcycle_type_select", "Tipo");
    this._fillSelect("select[name='type']", "Tipo");
    this._fillSelect("#id_sh_motorcycle_make_select", "Marca", true);
    this._fillSelect("select[name='make']", "Marca", true);
    this._fillSelect("#id_sh_motorcycle_year_select", "Año", true);
    this._fillSelect("select[name='year']", "Año", true);
    this._fillSelect("#id_sh_motorcycle_model_select", "Modelo", true);
    this._fillSelect("select[name='model']", "Modelo", true);
    $("#id_sh_motorcycle_go_submit_button").prop("disabled", true);
  },

  _fillSelect: function (selector, placeholder, disabled = false) {
    $(selector)
      .html(`<option value="">${placeholder}</option>`)
      .prop("disabled", disabled);
  },

  /*** CARGA LISTAS DE OPCIONES ***/

  loadTypeList: function () {
    rpc("/sh_motorcycle/get_type_list").then((data) => {
      data.forEach((type) => {
        $("#id_sh_motorcycle_type_select, select[name='type']").append(
          `<option value="${type.id}">${type.name}</option>`
        );
      });
    });
  },

  loadMakeList: function (type_id) {
    if (!type_id) return;
    this._fillSelect("#id_sh_motorcycle_make_select", "Marca");
    this._fillSelect("select[name='make']", "Marca");

    rpc("/sh_motorcycle/get_make_list", { type_id }).then((data) => {
      data.forEach((make) => {
        $("#id_sh_motorcycle_make_select, select[name='make']").append(
          `<option value="${make.id}">${make.name}</option>`
        );
      });
    });
  },

  loadYearList: function (type_id, make_id) {
    if (!type_id || !make_id) return;
    this._fillSelect("#id_sh_motorcycle_year_select", "Año");
    this._fillSelect("select[name='year']", "Año");

    rpc("/sh_motorcycle/get_year_list", { type_id, make_id }).then((data) => {
      data.forEach((year) => {
        $("#id_sh_motorcycle_year_select, select[name='year']").append(
          `<option value="${year}">${year}</option>`
        );
      });
    });
  },

  loadModelList: function (type_id, make_id, year) {
    if (!type_id || !make_id || !year) return;
    this._fillSelect("#id_sh_motorcycle_model_select", "Modelo");
    this._fillSelect("select[name='model']", "Modelo");

    rpc("/sh_motorcycle/get_model_list", { type_id, make_id, year }).then(
      (data) => {
        if (data.length === 0) {
          $("#id_sh_motorcycle_model_select, select[name='model']").prop(
            "disabled",
            true
          );
          $("#id_sh_motorcycle_model_select").after(
            '<small id="no_model_message" class="text-danger">No hay modelos disponibles.</small>'
          );
        } else {
          data.forEach((model) => {
            $("#id_sh_motorcycle_model_select, select[name='model']").append(
              `<option value="${model.id}">${model.name}</option>`
            );
          });
          $("#id_sh_motorcycle_model_select, select[name='model']").prop(
            "disabled",
            false
          );
        }
      }
    );
  },

  /*** EVENTOS ***/

  _onChangeType: function () {
    const type_id =
      $("#id_sh_motorcycle_type_select").val() ||
      $("select[name='type']").val();
    this.loadMakeList(type_id);
    this._fillSelect("#id_sh_motorcycle_year_select", "Año", true);
    this._fillSelect("#id_sh_motorcycle_model_select", "Modelo", true);
  },

  _onChangeMake: function () {
    const type_id =
      $("#id_sh_motorcycle_type_select").val() ||
      $("select[name='type']").val();
    const make_id =
      $("#id_sh_motorcycle_make_select").val() ||
      $("select[name='make']").val();
    this.loadYearList(type_id, make_id);
    this._fillSelect("#id_sh_motorcycle_model_select", "Modelo", true);
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
