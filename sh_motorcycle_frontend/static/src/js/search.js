/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

publicWidget.registry.sh_motorcycle_shop_search = publicWidget.Widget.extend({
  selector: "#wrap",
  events: {
    "change #id_sh_motorcycle_type_select": "_onChangeTypeGetMake",
    "change #id_sh_motorcycle_make_select": "_onChangeMakeGetModel",
    "change #id_sh_motorcycle_model_select": "_onChangeModelGetYear",
    "change #id_sh_motorcycle_year_select": "_onChangeYear",
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

    //when document reload or page refresh
    var result = self.getQueryString();
    rpc("/sh_motorcycle/is_bike_already_in_garage", {
      type_id: result["type"],
      make_id: result["make"],
      model_id: result["model"],
      year_id: result["year"],
    }).then(function (rec) {
      if (rec.is_bike_already_in_garage) {
        $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
      } else {
        $("#id_sh_motorcycle_save_bike_to_garage_btn").show();
      }
    });
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

  _onChangeMakeGetModel: function (e) {
    var self = this;
    e.preventDefault();

    //clean model
    $("#id_sh_motorcycle_model_select > option").not(":first").remove();

    //clean year
    $("#id_sh_motorcycle_year_select > option").not(":first").remove();

    rpc("/sh_motorcycle/get_model_list", {
      type_id: $("#id_sh_motorcycle_type_select > option:selected").val(),
      make_id: $("#id_sh_motorcycle_make_select > option:selected").val(),
    }).then(function (data) {
      jQuery.each(data, function (key, value) {
        $("#id_sh_motorcycle_model_select").append(
          '<option value="' + value.id + '">' + value.name + "</option>"
        );
      });
      self.diable_select_options();
    });
  },

  _onChangeModelGetYear: function (e) {
    var self = this;
    e.preventDefault();

    //clean year
    $("#id_sh_motorcycle_year_select > option").not(":first").remove();

    rpc("/sh_motorcycle/get_year_list", {
      type_id: $("#id_sh_motorcycle_type_select > option:selected").val(),
      make_id: $("#id_sh_motorcycle_make_select > option:selected").val(),
      model_id: $("#id_sh_motorcycle_model_select > option:selected").val(),
    }).then(function (data) {
      jQuery.each(data, function (key, value) {
        $("#id_sh_motorcycle_year_select").append(
          '<option value="' + value + '">' + value + "</option>"
        );
      });
      self.diable_select_options();
    });
  },

  _onChangeYear: function (e) {
    var self = this;
    e.preventDefault();
    self.diable_select_options();
  },

  _onClickSelectDiffVehicle: function () {
    var self = this;
    $("#id_sh_motorcycle_search_diff_bike_div").toggle();
    $("#id_sh_motorcycle_select_diff_bike_btn").toggle();
    self.save_bike_to_garage_btn_old_style = $(
      "#id_sh_motorcycle_save_bike_to_garage_btn"
    ).css("display");
    $("#id_sh_motorcycle_save_bike_to_garage_btn").hide();
    self.get_param_from_vehicle();
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
      year_id: result["year"],
    }).then(function (rec) {
      //refresh the page
      location.reload(true);
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
    var selectedOptions = false;

    //make
    var selectedOptions = $(
      "#id_sh_motorcycle_type_select > option:selected"
    ).val();
    if (selectedOptions == false) {
      $("#id_sh_motorcycle_make_select").prop("disabled", true);
    } else {
      $("#id_sh_motorcycle_make_select").prop("disabled", false);
    }

    //model
    var selectedOptions = $(
      "#id_sh_motorcycle_make_select > option:selected"
    ).val();
    if (selectedOptions == false) {
      $("#id_sh_motorcycle_model_select").prop("disabled", true);
    } else {
      $("#id_sh_motorcycle_model_select").prop("disabled", false);
    }

    //year
    var selectedOptions = $(
      "#id_sh_motorcycle_model_select > option:selected"
    ).val();
    if (selectedOptions == false) {
      $("#id_sh_motorcycle_year_select").prop("disabled", true);
    } else {
      $("#id_sh_motorcycle_year_select").prop("disabled", false);
    }

    //go button
    var selectedOptions = $(
      "#id_sh_motorcycle_year_select > option:selected"
    ).val();
    if (selectedOptions == false) {
      $("#id_sh_motorcycle_go_submit_button").prop("disabled", true);
    } else {
      $("#id_sh_motorcycle_go_submit_button").prop("disabled", false);
    }
  },

  _onClickRemoveVehicle: async function (ev) {
    var self = this;
    var motorcycle_id = $(ev.currentTarget).data("motorcycle_id");
    this.call("dialog", "add", ConfirmationDialog, {
      body: _t("Are you sure you want to remove the vehicle?"),
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
