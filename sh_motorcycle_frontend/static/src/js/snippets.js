/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.sh_motorcycle_frontend_tmpl_1 = publicWidget.Widget.extend({
    selector: "#sh_motorcycle_snippet_section_1",
    start: function () {
        this._super.apply(this, arguments);
        var self = this;

        rpc("/sh_motorcycle/is_user_logined_in").then(function (rec) {
            if (rec.is_user_logined_in){
                $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").hide();
                $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").show();
            } else {
                $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").show();
                $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").hide();
            }

            if (!rec.sh_is_show_garage){
                $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").hide();
                $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").hide();
            }
        });

        /* add category to select saved bike button. */

        $("#id_sh_motorcycle_snippet_select_saved_bike_div > a").remove();

        rpc("/sh_motorcycle/get_saved_bike").then(function (data) {
            jQuery.each(data, function (key, value) {
                $("#id_sh_motorcycle_snippet_select_saved_bike_div").append('<a class="dropdown-item" href="' + value.moto_url + '">' + value.name + "</a>");
            });

            //category selected in snippet options.
            var categ_id = $('input[id="id_input_sh_moto_categ_id"]').val();
            if (categ_id && categ_id.length) {
                var alinks = $("#id_sh_motorcycle_snippet_select_saved_bike_div").children("a");
                if (alinks) {
                    alinks.each(function (index) {
                        var href = $(this).attr("href");
                        href = href + "&category=" + categ_id;
                        $(this).attr("href", href);
                    });
                }
            }
        });
    },
});
