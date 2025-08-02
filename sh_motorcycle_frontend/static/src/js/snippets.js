/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.sh_motorcycle_frontend_tmpl_1 =
  publicWidget.Widget.extend({
    selector: "#sh_motorcycle_snippet_section_1",

    events: {
      // Eventos específicos para el manejo del garage
      "click #id_sh_motorcycle_snippet_select_saved_bike_dropdown":
        "_onClickGarageDropdown",
      "show.bs.dropdown #id_sh_motorcycle_snippet_select_saved_bike_dropdown":
        "_onShowGarageDropdown",
      "hide.bs.dropdown #id_sh_motorcycle_snippet_select_saved_bike_dropdown":
        "_onHideGarageDropdown",
    },

    init: function () {
      this._super(...arguments);
      // Flag para evitar llamadas múltiples
      this._isInitialized = false;
    },

    start: function () {
      this._super.apply(this, arguments);

      if (this._isInitialized) {
        return Promise.resolve();
      }

      this._isInitialized = true;
      return this._initializeGarageFeature();
    },

    /**
     * Inicializa toda la funcionalidad del garage
     * @private
     */
    _initializeGarageFeature: function () {
      const self = this;

      return rpc("/sh_motorcycle/is_user_logined_in")
        .then(function (rec) {
          console.log("Estado del usuario:", rec);

          if (rec.is_user_logined_in) {
            self._showLoggedInState();
          } else {
            self._showLoggedOutState();
          }

          // Si la funcionalidad está deshabilitada globalmente
          if (!rec.sh_is_show_garage) {
            self._hideGarageFeature();
          }

          // Cargar vehículos guardados solo si el usuario está logueado
          if (rec.is_user_logined_in && rec.sh_is_show_garage) {
            return self._loadSavedBikes();
          }
        })
        .catch(function (error) {
          console.error(
            "Error al inicializar funcionalidad del garage:",
            error
          );
          self._showLoggedOutState();
        });
    },

    /**
     * Muestra el estado cuando el usuario está logueado
     * @private
     */
    _showLoggedInState: function () {
      $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").hide();
      $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown")
        .show()
        .removeClass("disabled")
        .prop("disabled", false)
        .attr("data-bs-toggle", "dropdown")
        .attr("aria-expanded", "false");
    },

    /**
     * Muestra el estado cuando el usuario no está logueado
     * @private
     */
    _showLoggedOutState: function () {
      $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").show();
      $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").hide();
    },

    /**
     * Oculta completamente la funcionalidad del garage
     * @private
     */
    _hideGarageFeature: function () {
      $("#id_sh_motorcycle_snippet_login_to_acc_garage_link").hide();
      $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown").hide();
    },

    /**
     * Carga los vehículos guardados del usuario
     * @private
     */
    _loadSavedBikes: function () {
      const self = this;

      // Limpiar elementos existentes
      $("#id_sh_motorcycle_snippet_select_saved_bike_div > a").remove();

      return rpc("/sh_motorcycle/get_saved_bike")
        .then(function (data) {
          console.log("Vehículos cargados:", data);

          if (data && data.length > 0) {
            // Procesar cada vehículo
            data.forEach(function (bike) {
              self._addBikeToDropdown(bike);
            });

            // Aplicar categoría si está definida
            self._applyCategoryFilter();

            // Habilitar el dropdown
            self._enableGarageDropdown();
          } else {
            // No hay vehículos guardados
            self._addEmptyStateToDropdown();
            self._disableGarageDropdown();
          }
        })
        .catch(function (error) {
          console.error("Error al cargar vehículos:", error);
          self._addErrorStateToDropdown();
          self._disableGarageDropdown();
        });
    },

    /**
     * Agrega un vehículo al dropdown
     * @private
     * @param {Object} bike - Datos del vehículo
     */
    _addBikeToDropdown: function (bike) {
      const $dropdown = $("#id_sh_motorcycle_snippet_select_saved_bike_div");
      const $item = $(
        `<a class="dropdown-item" href="${bike.moto_url}">${bike.name}</a>`
      );

      // Agregar evento hover para mejor UX
      $item.hover(
        function () {
          $(this).addClass("bg-light");
        },
        function () {
          $(this).removeClass("bg-light");
        }
      );

      $dropdown.append($item);
    },

    /**
     * Agrega el estado vacío al dropdown
     * @private
     */
    _addEmptyStateToDropdown: function () {
      $("#id_sh_motorcycle_snippet_select_saved_bike_div").append(
        '<span class="dropdown-item-text text-muted small">No hay vehículos guardados</span>'
      );
    },

    /**
     * Agrega el estado de error al dropdown
     * @private
     */
    _addErrorStateToDropdown: function () {
      $("#id_sh_motorcycle_snippet_select_saved_bike_div").append(
        '<span class="dropdown-item-text text-danger small">Error al cargar vehículos</span>'
      );
    },

    /**
     * Habilita el dropdown del garage
     * @private
     */
    _enableGarageDropdown: function () {
      $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown")
        .removeClass("disabled")
        .prop("disabled", false)
        .attr("data-bs-toggle", "dropdown");
    },

    /**
     * Deshabilita el dropdown del garage
     * @private
     */
    _disableGarageDropdown: function () {
      $("#id_sh_motorcycle_snippet_select_saved_bike_dropdown")
        .addClass("disabled")
        .prop("disabled", true)
        .removeAttr("data-bs-toggle");
    },

    /**
     * Aplica el filtro de categoría si está definido
     * @private
     */
    _applyCategoryFilter: function () {
      const categ_id = $('input[id="id_input_sh_moto_categ_id"]').val();

      if (categ_id && categ_id.length) {
        const $links = $(
          "#id_sh_motorcycle_snippet_select_saved_bike_div"
        ).children("a");

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

    /**
     * Maneja el click en el dropdown del garage
     * @private
     * @param {Event} ev
     */
    _onClickGarageDropdown: function (ev) {
      console.log("Click en dropdown garage");

      const $target = $(ev.currentTarget);

      // Si está deshabilitado, prevenir acción
      if ($target.hasClass("disabled") || $target.prop("disabled")) {
        ev.preventDefault();
        ev.stopPropagation();
        console.log("Dropdown deshabilitado");
        return false;
      }

      // Verificar si hay contenido en el dropdown
      const hasContent =
        $("#id_sh_motorcycle_snippet_select_saved_bike_div > a").length > 0;

      if (!hasContent) {
        ev.preventDefault();
        ev.stopPropagation();
        console.log("Sin contenido en dropdown");
        return false;
      }

      // El dropdown debería funcionar normalmente
      console.log("Dropdown funcionando correctamente");
    },

    /**
     * Maneja cuando se muestra el dropdown
     * @private
     * @param {Event} ev
     */
    _onShowGarageDropdown: function (ev) {
      console.log("Dropdown mostrado");
      // Aquí podrías agregar lógica adicional cuando se abre el dropdown
    },

    /**
     * Maneja cuando se oculta el dropdown
     * @private
     * @param {Event} ev
     */
    _onHideGarageDropdown: function (ev) {
      console.log("Dropdown ocultado");
      // Aquí podrías agregar lógica adicional cuando se cierra el dropdown
    },

    /**
     * Método público para recargar los vehículos
     * @public
     */
    reloadSavedBikes: function () {
      return this._loadSavedBikes();
    },

    /**
     * Método público para verificar el estado del usuario
     * @public
     */
    checkUserStatus: function () {
      return this._initializeGarageFeature();
    },
  });
