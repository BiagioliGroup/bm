/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

publicWidget.registry.sh_motorcycle_shop_search = publicWidget.Widget.extend({
  selector: "#wrap",

  events: {
    "change #id_sh_motorcycle_type": "_onChangeType",
    "change #id_sh_motorcycle_make": "_onChangeMake",
    "change #id_sh_motorcycle_year": "_onChangeYear",
    "change #id_sh_motorcycle_model": "_onChangeModel",

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

    // Eventos para ambos botones Mi Garage (fase 1 y fase 2)
    "click #id_sh_motorcycle_select_saved_bike_btn": "_onClickMyGarage",
    "click #id_sh_motorcycle_select_saved_bike_btn_phase2":
      "_onClickMyGaragePhase2",
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
    this._initializeMyGarageButtons();
  },

  /*** INICIALIZACIÓN DE AMBOS BOTONES MI GARAGE ***/
  _initializeMyGarageButtons: function () {
    const self = this;

    rpc("/sh_motorcycle/is_user_logined_in")
      .then(function (rec) {
        console.log("Estado del usuario:", rec);

        if (rec.is_user_logined_in) {
          // Habilitar botón de fase 1
          $("#id_sh_motorcycle_select_saved_bike_btn")
            .removeClass("disabled")
            .prop("disabled", false)
            .attr("data-bs-toggle", "dropdown")
            .attr("aria-expanded", "false");

          // Habilitar botón de fase 2
          $("#id_sh_motorcycle_select_saved_bike_btn_phase2")
            .removeClass("disabled")
            .prop("disabled", false)
            .attr("data-bs-toggle", "dropdown")
            .attr("aria-expanded", "false");

          // Cargar los vehículos guardados para ambas fases
          self._loadSavedBikes();
        } else {
          // Deshabilitar ambos botones
          $(
            "#id_sh_motorcycle_select_saved_bike_btn, #id_sh_motorcycle_select_saved_bike_btn_phase2"
          )
            .addClass("disabled")
            .prop("disabled", true)
            .removeAttr("data-bs-toggle");
        }
      })
      .catch(function (error) {
        console.error("Error al verificar el estado del usuario:", error);
        // En caso de error, deshabilitar ambos botones
        $(
          "#id_sh_motorcycle_select_saved_bike_btn, #id_sh_motorcycle_select_saved_bike_btn_phase2"
        )
          .addClass("disabled")
          .prop("disabled", true)
          .removeAttr("data-bs-toggle");
      });
  },

  /*** MANEJADOR DEL CLICK EN MI GARAGE - FASE 1 ***/
  _onClickMyGarage: function (ev) {
    return this._handleMyGarageClick(
      ev,
      "#id_sh_motorcycle_select_saved_bike_div"
    );
  },

  /*** MANEJADOR DEL CLICK EN MI GARAGE - FASE 2 ***/
  _onClickMyGaragePhase2: function (ev) {
    return this._handleMyGarageClick(
      ev,
      "#id_sh_motorcycle_select_saved_bike_div_phase2"
    );
  },

  /*** LÓGICA COMÚN PARA AMBOS BOTONES MI GARAGE ***/
  _handleMyGarageClick: function (ev, dropdownSelector) {
    console.log("Mi Garage clickeado:", dropdownSelector);

    const $target = $(ev.currentTarget);

    // Si el botón está deshabilitado, no hacer nada
    if ($target.hasClass("disabled") || $target.prop("disabled")) {
      ev.preventDefault();
      ev.stopPropagation();
      console.log("Botón deshabilitado");
      return false;
    }

    // Verificar si hay vehículos en el dropdown
    const $dropdownMenu = $(dropdownSelector);
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
    this.renderSelect($("#id_sh_motorcycle_type"), [], "Tipo");
    this.renderSelect($("select[name='type']"), [], "Tipo");
    this.renderSelect($("#id_sh_motorcycle_make"), [], "Marca", true);
    this.renderSelect($("select[name='make']"), [], "Marca", true);
    this.renderSelect($("#id_sh_motorcycle_year"), [], "Año", true);
    this.renderSelect($("select[name='year']"), [], "Año", true);
    this.renderSelect($("#id_sh_motorcycle_model"), [], "Modelo", true);
    this.renderSelect($("select[name='model']"), [], "Modelo", true);
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
      this.renderSelect($("#id_sh_motorcycle_type"), data, "Tipo");
      this.renderSelect($("select[name='type']"), data, "Tipo");
    });
  },

  loadMakeList: function (type_id) {
    if (!type_id) return;
    rpc("/sh_motorcycle/get_make_list", { type_id }).then((data) => {
      this.renderSelect($("#id_sh_motorcycle_make"), data, "Marca");
      this.renderSelect($("select[name='make']"), data, "Marca");
    });
  },

  loadYearList: function (type_id, make_id) {
    if (!type_id || !make_id) return;
    rpc("/sh_motorcycle/get_year_list", { type_id, make_id }).then((data) => {
      this.renderSelect($("#id_sh_motorcycle_year"), data, "Año");
      this.renderSelect($("select[name='year']"), data, "Año");
    });
  },

  loadModelList: function (type_id, make_id, year) {
    if (!type_id || !make_id || !year) return;
    rpc("/sh_motorcycle/get_model_list", { type_id, make_id, year }).then(
      (data) => {
        this.renderSelect($("#id_sh_motorcycle_model"), data, "Modelo");
        this.renderSelect($("select[name='model']"), data, "Modelo");
      }
    );
  },

  /*** EVENTOS ***/
  _onChangeType: function () {
    const type_id =
      $("#id_sh_motorcycle_type").val() || $("select[name='type']").val();
    this.loadMakeList(type_id);
    this.renderSelect($("#id_sh_motorcycle_year"), [], "Año", true);
    this.renderSelect($("select[name='year']"), [], "Año", true);
    this.renderSelect($("#id_sh_motorcycle_model"), [], "Modelo", true);
    this.renderSelect($("select[name='model']"), [], "Modelo", true);
  },

  _onChangeMake: function () {
    const type_id =
      $("#id_sh_motorcycle_type").val() || $("select[name='type']").val();
    const make_id =
      $("#id_sh_motorcycle_make").val() || $("select[name='make']").val();
    this.loadYearList(type_id, make_id);
    this.renderSelect($("#id_sh_motorcycle_model"), [], "Modelo", true);
    this.renderSelect($("select[name='model']"), [], "Modelo", true);
  },

  _onChangeYear: function () {
    const type_id =
      $("#id_sh_motorcycle_type").val() || $("select[name='type']").val();
    const make_id =
      $("#id_sh_motorcycle_make").val() || $("select[name='make']").val();
    const year =
      $("#id_sh_motorcycle_year").val() || $("select[name='year']").val();
    this.loadModelList(type_id, make_id, year);
  },

  _onChangeModel: function () {
    const model_id =
      $("#id_sh_motorcycle_model").val() || $("select[name='model']").val();
    // Habilitar botón de búsqueda cuando se selecciona modelo
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

    // Limpiar elementos existentes en ambos dropdowns
    $(
      "#id_sh_motorcycle_select_saved_bike_div > a, #id_sh_motorcycle_select_saved_bike_div_phase2 > a"
    ).remove();

    return rpc("/sh_motorcycle/get_saved_bike")
      .then((data) => {
        console.log("Vehículos recibidos:", data);

        if (data && data.length > 0) {
          // Agregar vehículos a ambos dropdowns
          data.forEach((bike) => {
            const vehicleLink = `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`;
            $("#id_sh_motorcycle_select_saved_bike_div").append(vehicleLink);
            $("#id_sh_motorcycle_select_saved_bike_div_phase2").append(
              vehicleLink
            );
          });

          // Aplicar filtro de categoría si existe
          this._applyCategoryFilter();

          // Habilitar ambos botones
          $(
            "#id_sh_motorcycle_select_saved_bike_btn, #id_sh_motorcycle_select_saved_bike_btn_phase2"
          )
            .removeClass("disabled")
            .prop("disabled", false)
            .attr("data-bs-toggle", "dropdown");

          console.log("Vehículos cargados correctamente en ambas fases");
        } else {
          // No hay vehículos - agregar mensaje informativo en ambos dropdowns
          const emptyMessage = `<span class="dropdown-item-text text-muted">No hay vehículos guardados</span>`;
          $("#id_sh_motorcycle_select_saved_bike_div").append(emptyMessage);
          $("#id_sh_motorcycle_select_saved_bike_div_phase2").append(
            emptyMessage
          );

          console.log("No se encontraron vehículos guardados");
        }
      })
      .catch(function (error) {
        console.error("Error al cargar vehículos guardados:", error);
        // En caso de error, agregar mensaje de error en ambos dropdowns
        const errorMessage = `<span class="dropdown-item-text text-danger">Error al cargar vehículos</span>`;
        $("#id_sh_motorcycle_select_saved_bike_div").append(errorMessage);
        $("#id_sh_motorcycle_select_saved_bike_div_phase2").append(
          errorMessage
        );
      });
  },

  _applyCategoryFilter: function () {
    const categ_id = $('input[id="id_input_sh_moto_categ_id"]').val();

    if (categ_id && categ_id.length) {
      // Aplicar filtro a ambos dropdowns
      const $links = $(
        "#id_sh_motorcycle_select_saved_bike_div > a, #id_sh_motorcycle_select_saved_bike_div_phase2 > a"
      );

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

// Función global para compatibilidad
window.loadGarageVehicles = function () {
  console.log("loadGarageVehicles llamada - redirigiendo al widget");

  rpc("/sh_motorcycle/get_saved_bike").then((data) => {
    $(
      "#id_sh_motorcycle_select_saved_bike_div > a, #id_sh_motorcycle_select_saved_bike_div_phase2 > a"
    ).remove();
    if (data && data.length > 0) {
      data.forEach((bike) => {
        const vehicleLink = `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`;
        $("#id_sh_motorcycle_select_saved_bike_div").append(vehicleLink);
        $("#id_sh_motorcycle_select_saved_bike_div_phase2").append(vehicleLink);
      });
    }
  });
};
