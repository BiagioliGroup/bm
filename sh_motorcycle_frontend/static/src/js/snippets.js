/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

// Widget para snippets - funcionalidad básica sin conflictos
publicWidget.registry.sh_motorcycle_frontend_tmpl_1 =
  publicWidget.Widget.extend({
    selector: "#sh_motorcycle_snippet_section_1",

    init: function () {
      this._super(...arguments);
      this._isInitialized = false;
    },

    start: function () {
      this._super.apply(this, arguments);

      // Evitar inicialización múltiple
      if (this._isInitialized) {
        return Promise.resolve();
      }

      this._isInitialized = true;

      // Solo ejecutar si estamos en el contexto de snippet y no en la página de shop
      if (this.$el.length > 0 && !$("#wrap").hasClass("shop-page")) {
        return this._initializeSnippetFeatures();
      }

      return Promise.resolve();
    },

    /**
     * Inicializa funcionalidades específicas del snippet
     * @private
     */
    _initializeSnippetFeatures: function () {
      const self = this;

      return rpc("/sh_motorcycle/is_user_logined_in")
        .then(function (rec) {
          // Solo manejar los elementos específicos del snippet
          if (rec.is_user_logined_in) {
            $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").hide();
            $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").show();
          } else {
            $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").show();
            $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").hide();
          }

          if (!rec.sh_is_show_garage) {
            $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").hide();
            $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").hide();
          }

          // Solo cargar vehículos para el snippet dropdown si el usuario está logueado
          if (rec.is_user_logined_in && rec.sh_is_show_garage) {
            return self._loadSnippetSavedBikes();
          }
        })
        .catch(function (error) {
          console.error("Error en snippet initialization:", error);
        });
    },

    /**
     * Carga vehículos específicamente para el snippet dropdown
     * @private
     */
    _loadSnippetSavedBikes: function () {
      // Solo procesar si existe el elemento del snippet
      const $snippetDiv = $("#id_sh_motorcycle_snippet_select_saved_bike_div");
      if ($snippetDiv.length === 0) {
        return Promise.resolve();
      }

      // Limpiar solo los elementos del snippet
      $snippetDiv.find("> a").remove();

      return rpc("/sh_motorcycle/get_saved_bike")
        .then(function (data) {
          if (data && data.length > 0) {
            data.forEach(function (bike) {
              $snippetDiv.append(
                `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`
              );
            });

            // Aplicar categoría solo para el snippet
            const categ_id = $('input[id="id_input_sh_moto_categ_id"]').val();
            if (categ_id && categ_id.length) {
              $snippetDiv.children("a").each(function () {
                const $link = $(this);
                let href = $link.attr("href");
                if (href && !href.includes("category=")) {
                  href = href + "&category=" + categ_id;
                  $link.attr("href", href);
                }
              });
            }
          } else {
            $snippetDiv.append(
              '<span class="dropdown-item-text text-muted">No hay vehículos guardados</span>'
            );
          }
        })
        .catch(function (error) {
          console.error("Error cargando vehículos del snippet:", error);
        });
    },
  });
