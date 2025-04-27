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
    $("#id_sh_motorcycle_type_select > option").not(":first").remove();

    rpc("/sh_motorcycle/get_type_list").then(function (data) {
      jQuery.each(data, function (key, value) {
        $("#id_sh_motorcycle_type_select").append(
          '<option  value="' + value.id + '">' + value.name + "</option>"
        );
      });
    });
    $(".id_sh_motorcycle_save_bike_to_garage_btn").css("display");
    self.diable_select_options();

    // when document reload or page refresh
    var result = self.getQueryString();

    // Mostrar el botón solo si hay búsqueda completa
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
      // Ocultar el botón si falta alguno de los campos
      $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
    }

    // limpiar links anteriores
    $("#id_sh_motorcycle_select_saved_bike_div > a").remove();

    // cargar links de motos guardadas
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

  _onChangeTypeGetMake: function (e) {
    var self = this;
    e.preventDefault();

    //clean make
    $("#id_sh_motorcycle_make_select > option").not(":first").remove();

    //clean model
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();

    //clean year
    $("#id_sh_motorcycle_year_select > option").not(":first").remove();

    rpc("/sh_motorcycle/get_make_list", {
      type_id: $("#id_sh_motorcycle_type_select > option:selected").val(),
    }).then(function (data) {
      jQuery.each(data, function (key, value) {
        $("#id_sh_motorcycle_make_select").append(
          '<option value="' + value.id + '">' + value.name + "</option>"
        );
      });
      self.diable_select_options();
    });
  },

  _onChangeMakeGetYear: function (e) {
    e.preventDefault();
    // Limpia año y modelo
    $("#id_sh_motorcycle_year_select > option").not(":first").remove();
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();
    // Carga años para tipo+marca
    rpc("/sh_motorcycle/get_year_list", {
      type_id: $("#id_sh_motorcycle_type_select").val(),
      make_id: $("#id_sh_motorcycle_make_select").val(),
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

    // Limpia modelo
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();
    $("#no_model_message").remove(); // 🔥 eliminar mensajes anteriores

    // Carga modelos para tipo+marca+año
    rpc("/sh_motorcycle/get_model_list", {
      type_id: $("#id_sh_motorcycle_type_select").val(),
      make_id: $("#id_sh_motorcycle_make_select").val(),
      year: $("#id_sh_motorcycle_year_select").val(),
    }).then((data) => {
      if (data.length === 0) {
        // 🔥 Si no hay modelos, mostramos mensaje
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

        // 🔥 Si hay solo uno, lo seleccionamos automáticamente
        if (data.length === 1) {
          $("#id_sh_motorcycle_model_select").val(data[0].id);
        }
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

    // Mostrar/Ocultar el bloque de selección diferente
    $("#id_sh_motorcycle_search_diff_bike_div").toggle();
    $("#id_sh_motorcycle_select_diff_bike_btn").toggle();

    // Guardar estilo previo del botón
    self.save_bike_to_garage_btn_old_style = $(
      "#id_sh_motorcycle_save_bike_to_garage_btn"
    ).css("display");
    $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();

    // 🔥 Limpiar todos los selectores
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

    // 🔥 Eliminar mensajes anteriores si existían
    $("#no_model_message").remove();

    // Volver a cargar solo los tipos de vehículos
    $("#id_sh_motorcycle_type_select > option").not(":first").remove();
    rpc("/sh_motorcycle/get_type_list").then(function (data) {
      jQuery.each(data, function (key, value) {
        $("#id_sh_motorcycle_type_select").append(
          '<option value="' + value.id + '">' + value.name + "</option>"
        );
      });
    });

    self.diable_select_options();

    // 🔥 Limpiar URL y recargar página
    window.location.href = "/shop";
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

  _onClickSaveBikeToGarage: function (ev) {
    var self = this;
    var result = self.getQueryString();

    rpc("/sh_motorcycle/add_bike_to_garage", {
      type_id: result["type"],
      make_id: result["make"],
      model_id: result["model"],
      year: result["year"],
    }).then(function (rec) {
      // Oculta el botón una vez guardado
      $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();

      // Redirige como si se hubiera hecho clic en la lupa
      var query = $.param(result); // convierte el objeto en query string
      window.location.href = "/shop?" + query;
    });
  },

  get_param_from_vehicle: function () {
    var searchParams = new URLSearchParams(window.location.search);
    var paramType = searchParams.get("type");
    var paramMake = searchParams.get("make");
    var paramModel = searchParams.get("model");
    var paramYear = searchParams.get("year");

    setTimeout(function () {
      if (paramType > 0) {
        var selected = $(document)
          .find(
            '#id_sh_motorcycle_search_diff_bike_form #id_sh_motorcycle_type_select option[value="' +
              paramType +
              '"]'
          )
          .attr("selected", "true");
        if (selected) {
          var x = $(document)
            .find(
              "#id_sh_motorcycle_search_diff_bike_form #id_sh_motorcycle_make_select"
            )
            .prop("disabled", false);
        }
      }
      if (paramMake > 0) {
        $(document)
          .find(
            '#id_sh_motorcycle_search_diff_bike_form #id_sh_motorcycle_make_select option[value="' +
              paramMake +
              '"]'
          )
          .attr("selected", "true");
      }
      if (paramModel > 0) {
        $(document)
          .find(
            '#id_sh_motorcycle_search_diff_bike_form #id_sh_motorcycle_model_select option[value="' +
              paramModel +
              '"]'
          )
          .attr("selected", "true");
      }
      if (paramYear > 0) {
        $(document)
          .find(
            '#id_sh_motorcycle_search_diff_bike_form #id_sh_motorcycle_year_select option[value="' +
              paramYear +
              '"]'
          )
          .attr("selected", "true");
      }
    }, 500);
  },

  diable_select_options: function () {
    // Marca
    var typeSelected = $(
      "#id_sh_motorcycle_type_select > option:selected"
    ).val();
    if (typeSelected) {
      $("#id_sh_motorcycle_make_select").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_make_select").prop("disabled", true);
    }

    // Año
    var makeSelected = $(
      "#id_sh_motorcycle_make_select > option:selected"
    ).val();
    if (makeSelected) {
      $("#id_sh_motorcycle_year_select").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_year_select").prop("disabled", true);
    }

    // Modelo
    var yearSelected = $(
      "#id_sh_motorcycle_year_select > option:selected"
    ).val();
    if (yearSelected) {
      $("#id_sh_motorcycle_model_select").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_model_select").prop("disabled", true);
    }

    // Botón Ir
    var modelSelected = $(
      "#id_sh_motorcycle_model_select > option:selected"
    ).val();
    if (modelSelected) {
      $("#id_sh_motorcycle_go_submit_button").prop("disabled", false);
    } else {
      $("#id_sh_motorcycle_go_submit_button").prop("disabled", true);
    }
  },

  _onClickRemoveVehicle: async function (ev) {
    var self = this;
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

    // new Dialog(this, {
    //   title: _t("Confirmation"),
    //   $content: $(
    //     "<p>" + _t("Are you sure you want to remove the vehicle?") + "</p>"
    //   ),
    //   buttons: [
    //     {
    //       text: _t("Yes"),
    //       classes: "btn-primary",
    //       click: async (ev) => {
    //         console.log("\n\n motorcycle_id ==", motorcycle_id);
    //         window.location.href = "/my/garage/remove_bike?id=" + motorcycle_id;
    //       },
    //     },
    //     { text: _t("Cancel"), close: true },
    //   ],
    // }).open();
  },
});
