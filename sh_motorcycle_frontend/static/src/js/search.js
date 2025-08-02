/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

// Widget principal para la búsqueda de motocicletas
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
    "click .id_sh_motorcycle_search_diff_bike_close":
      "_onClickSelectDiffVehicleClose",
    "click #id_sh_motorcycle_save_bike_to_garage_btn":
      "_onClickSaveBikeToGarage",
    "click .js_cls_remove_vehicle_button": "_onClickRemoveVehicle",

    // Eventos para el botón Mi Garage - usando los IDs correctos del template
    "click #id_sh_motorcycle_select_saved_bike_btn": "_onClickMyGarage",
  },

  init: function () {
    this._super(...arguments);
    this.dialog = this.bindService("dialog");
  },

  start: function () {
    this._super(...arguments);
    this._initializeSelectors();
    this._loadSavedBikes();
    this._checkSavedButton();
    this._initializeMyGarageButton();
  },

  /*** INICIALIZACIÓN DEL BOTÓN MI GARAGE ***/
  _initializeMyGarageButton: function () {
    const self = this;

    rpc("/sh_motorcycle/is_user_logined_in")
      .then(function (rec) {
        console.log("Estado del usuario:", rec);

        if (rec.is_user_logined_in) {
          // Usuario logueado - habilitar el botón
          $("#id_sh_motorcycle_select_saved_bike_btn")
            .removeClass("disabled")
            .prop("disabled", false)
            .attr("data-bs-toggle", "dropdown")
            .attr("aria-expanded", "false");

          // Cargar los vehículos guardados
          self._loadSavedBikes();
        } else {
          // Usuario no logueado - deshabilitar el botón
          $("#id_sh_motorcycle_select_saved_bike_btn")
            .addClass("disabled")
            .prop("disabled", true)
            .removeAttr("data-bs-toggle");
        }
      })
      .catch(function (error) {
        console.error("Error al verificar el estado del usuario:", error);
        // En caso de error, deshabilitar el botón
        $("#id_sh_motorcycle_select_saved_bike_btn")
          .addClass("disabled")
          .prop("disabled", true)
          .removeAttr("data-bs-toggle");
      });
  },

  /*** MANEJADOR DEL CLICK EN MI GARAGE ***/
  _onClickMyGarage: function (ev) {
    console.log("Mi Garage clickeado");

    const $target = $(ev.currentTarget);

    // Si el botón está deshabilitado, no hacer nada
    if ($target.hasClass("disabled") || $target.prop("disabled")) {
      ev.preventDefault();
      ev.stopPropagation();
      console.log("Botón deshabilitado");
      return false;
    }

    // Verificar si hay vehículos en el dropdown
    const $dropdownMenu = $("#id_sh_motorcycle_select_saved_bike_div");
    const vehicleLinks = $dropdownMenu.find("a.dropdown-item:not(.text-muted)");

    if (vehicleLinks.length === 0) {
      ev.preventDefault();
      ev.stopPropagation();
      this._showNoVehiclesMessage();
      return false;
    }

    // Si todo está bien, Bootstrap manejará el dropdown automáticamente
    console.log("Dropdown funcionando correctamente");
  },

  /*** MOSTRAR MENSAJE CUANDO NO HAY VEHÍCULOS ***/
  _showNoVehiclesMessage: function () {
    this.dialog.add(ConfirmationDialog, {
      body: _t(
        "No tienes vehículos guardados en tu garage. ¿Quieres buscar uno ahora?"
      ),
      confirm: () => {
        this._onClickSelectDiffVehicle();
      },
      cancel: () => {},
      cancelLabel: _t("Cancelar"),
      confirmLabel: _t("Buscar Vehículo"),
    });
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
      // Recargar los vehículos guardados
      this._loadSavedBikes();
      window.location.href = "/shop?" + $.param(params);
    });
  },

  _onClickRemoveVehicle: async function (ev) {
    const motorcycle_id = $(ev.currentTarget).data("motorcycle_id");
    this.dialog.add(ConfirmationDialog, {
      body: _t("¿Estás seguro de eliminar este vehículo?"),
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
        if (key && value) {
          result[key] = decodeURIComponent(value);
        }
      });
    return result;
  },

  _loadSavedBikes: function () {
    console.log("Cargando vehículos guardados...");

    // Limpiar elementos existentes (excepto los placeholder del template)
    $("#id_sh_motorcycle_select_saved_bike_div > a").remove();

    return rpc("/sh_motorcycle/get_saved_bike")
      .then((data) => {
        console.log("Vehículos recibidos:", data);

        if (data && data.length > 0) {
          data.forEach((bike) => {
            $("#id_sh_motorcycle_select_saved_bike_div").append(
              `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`
            );
          });

          // Aplicar filtro de categoría si existe
          this._applyCategoryFilter();

          // Habilitar el botón
          $("#id_sh_motorcycle_select_saved_bike_btn")
            .removeClass("disabled")
            .prop("disabled", false)
            .attr("data-bs-toggle", "dropdown");

          console.log("Vehículos cargados correctamente");
        } else {
          // No hay vehículos - agregar mensaje informativo
          $("#id_sh_motorcycle_select_saved_bike_div").append(
            `<span class="dropdown-item-text text-muted">No hay vehículos guardados</span>`
          );

          console.log("No se encontraron vehículos guardados");
        }
      })
      .catch(function (error) {
        console.error("Error al cargar vehículos guardados:", error);
        // En caso de error, agregar mensaje de error
        $("#id_sh_motorcycle_select_saved_bike_div").append(
          `<span class="dropdown-item-text text-danger">Error al cargar vehículos</span>`
        );
      });
  },

  _applyCategoryFilter: function () {
    const categ_id = $('input[id="id_input_sh_moto_categ_id"]').val();

    if (categ_id && categ_id.length) {
      const $links = $("#id_sh_motorcycle_select_saved_bike_div > a");

      $links.each(function () {
        const $link = $(this);
        let href = $link.attr("href");

        if (href && !href.includes("category=")) {
          href = href + "&category=" + categ_id;
          $link.attr("href", href);
        }
      });
    }
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

// Función global para compatibilidad con posibles onclick en HTML
// Esta función previene el error "loadGarageVehicles is not defined"
window.loadGarageVehicles = function () {
  console.log("loadGarageVehicles llamada - redirigiendo al widget");

  // Buscar el widget activo
  const widget = publicWidget.registry.sh_motorcycle_shop_search;
  if (widget && widget.prototype._loadSavedBikes) {
    // Si existe una instancia del widget, usar su método
    const instance = $(".sh_motorcycle_shop_search").data("widget");
    if (instance && instance._loadSavedBikes) {
      instance._loadSavedBikes();
    } else {
      // Si no hay instancia, crear una temporal para cargar los vehículos
      console.log("Creando carga temporal de vehículos");
      rpc("/sh_motorcycle/get_saved_bike").then((data) => {
        $("#id_sh_motorcycle_select_saved_bike_div > a").remove();
        if (data && data.length > 0) {
          data.forEach((bike) => {
            $("#id_sh_motorcycle_select_saved_bike_div").append(
              `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`
            );
          });
        }
      });
    }
  }
};
