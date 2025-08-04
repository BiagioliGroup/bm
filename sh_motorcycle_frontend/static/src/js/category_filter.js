/** @odoo-module */

/**
 * 📂 FILTRADO DINÁMICO DE CATEGORÍAS POR VEHÍCULO
 * Se integra con el search.js existente para actualizar categorías
 */

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CategoryVehicleFilter = publicWidget.Widget.extend({
  selector: ".products_categories", // Selector específico para categorías
  events: {
    // No eventos propios - escucha cambios del search widget
  },

  /**
   * @override
   */
  start: function () {
    console.log("📂 Inicializando filtro de categorías por vehículo...");
    this._setupVehicleChangeListeners();
    this._initialCategoryFilter();
    return this._super.apply(this, arguments);
  },

  //--------------------------------------------------------------------------
  // Private
  //--------------------------------------------------------------------------

  /**
   * Configurar listeners para cambios en el buscador de vehículos
   * @private
   */
  _setupVehicleChangeListeners: function () {
    const self = this;

    // Escuchar cambios en selectores de vehículo
    const vehicleSelectors = [
      'select[name="type"]',
      'select[name="make"]',
      'select[name="model"]',
      'select[name="year"]',
    ];

    vehicleSelectors.forEach((selector) => {
      $(document).on("change", selector, function () {
        // Pequeño delay para que el search.js termine su trabajo
        setTimeout(() => {
          self._updateCategoriesBasedOnVehicle();
        }, 300);
      });
    });

    // También escuchar cuando se envía el formulario de búsqueda
    $(document).on(
      "submit",
      "#id_sh_motorcycle_search_form, #id_sh_motorcycle_search_diff_bike_form",
      function () {
        setTimeout(() => {
          self._updateCategoriesBasedOnVehicle();
        }, 500);
      }
    );
  },

  /**
   * Filtrado inicial de categorías al cargar la página
   * @private
   */
  _initialCategoryFilter: function () {
    // Verificar si ya hay un vehículo seleccionado en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const hasVehicleParams =
      urlParams.get("type") &&
      urlParams.get("make") &&
      urlParams.get("model") &&
      urlParams.get("year");

    if (hasVehicleParams) {
      this._updateCategoriesBasedOnVehicle();
    }
  },

  /**
   * Actualizar categorías basado en el vehículo seleccionado
   * @private
   */
  _updateCategoriesBasedOnVehicle: function () {
    const vehicleData = this._getCurrentVehicleSelection();

    console.log("📂 Actualizando categorías para vehículo:", vehicleData);

    // Si no hay vehículo completo seleccionado, mostrar todas las categorías
    if (!this._isVehicleComplete(vehicleData)) {
      this._showAllCategories();
      return;
    }

    // Obtener categorías filtradas del servidor
    rpc("/shop/categories/filtered", vehicleData)
      .then((result) => {
        this._updateCategoryDisplay(result);
      })
      .catch((error) => {
        console.error("Error al filtrar categorías:", error);
        this._showAllCategories(); // Fallback
      });
  },

  /**
   * Obtener la selección actual de vehículo
   * @private
   * @returns {Object} Datos del vehículo seleccionado
   */
  _getCurrentVehicleSelection: function () {
    // Intentar obtener de los selectores actuales
    let vehicleData = {
      type: $('select[name="type"]').val() || "",
      make: $('select[name="make"]').val() || "",
      model: $('select[name="model"]').val() || "",
      year: $('select[name="year"]').val() || "",
    };

    // Si no hay selectores visibles, obtener de la URL
    if (!vehicleData.type) {
      const urlParams = new URLSearchParams(window.location.search);
      vehicleData = {
        type: urlParams.get("type") || "",
        make: urlParams.get("make") || "",
        model: urlParams.get("model") || "",
        year: urlParams.get("year") || "",
      };
    }

    return vehicleData;
  },

  /**
   * Verificar si la selección de vehículo está completa
   * @private
   * @param {Object} vehicleData - Datos del vehículo
   * @returns {boolean}
   */
  _isVehicleComplete: function (vehicleData) {
    return (
      vehicleData.type &&
      vehicleData.make &&
      vehicleData.model &&
      vehicleData.year
    );
  },

  /**
   * Actualizar la visualización de categorías
   * @private
   * @param {Object} result - Resultado del servidor con categorías filtradas
   */
  _updateCategoryDisplay: function (result) {
    const $categoriesList = this.$(".wsale_products_categories_list");

    if (!result.categories || result.categories.length === 0) {
      this._showNoCategories();
      return;
    }

    // Ocultar categorías que no están en la lista filtrada
    this._hideNonMatchingCategories(result.categories);

    // Mostrar mensaje informativo
    this._showFilterInfo(result.total_categories, result.has_vehicle_filter);

    console.log(`📂 Mostrando ${result.total_categories} categorías filtradas`);
  },

  /**
   * Ocultar categorías que no coinciden con el filtro
   * @private
   * @param {Array} filteredCategories - Categorías que deben mostrarse
   */
  _hideNonMatchingCategories: function (filteredCategories) {
    const allowedIds = new Set();

    // Recopilar todos los IDs permitidos (incluyendo hijos)
    const collectIds = (categories) => {
      categories.forEach((category) => {
        allowedIds.add(category.id);
        if (category.children && category.children.length > 0) {
          collectIds(category.children);
        }
      });
    };
    collectIds(filteredCategories);

    // Ocultar/mostrar elementos de categoría
    this.$(".nav-item").each((index, element) => {
      const $item = $(element);
      const $link = $item.find('> a[href*="/shop/category/"]');

      if ($link.length > 0) {
        const href = $link.attr("href");
        const categoryId = this._extractCategoryIdFromUrl(href);

        if (categoryId && allowedIds.has(categoryId)) {
          $item.removeClass("d-none").show();
        } else {
          $item.addClass("d-none").hide();
        }
      }
    });
  },

  /**
   * Extraer ID de categoría de una URL
   * @private
   * @param {string} url - URL de categoría
   * @returns {number|null} ID de la categoría
   */
  _extractCategoryIdFromUrl: function (url) {
    // URL format: /shop/category/slug-ID
    const match = url.match(/\/shop\/category\/.*-(\d+)$/);
    return match ? parseInt(match[1]) : null;
  },

  /**
   * Mostrar todas las categorías (sin filtro)
   * @private
   */
  _showAllCategories: function () {
    this.$(".nav-item").removeClass("d-none").show();
    this._hideFilterInfo();
    console.log("📂 Mostrando todas las categorías");
  },

  /**
   * Mostrar mensaje cuando no hay categorías
   * @private
   */
  _showNoCategories: function () {
    // Ocultar todas las categorías
    this.$(".nav-item").addClass("d-none").hide();

    // Mostrar mensaje informativo
    if (this.$(".no-categories-message").length === 0) {
      const message = $(`
                <div class="no-categories-message alert alert-info text-center mt-3">
                    <i class="fa fa-info-circle"></i>
                    No hay categorías disponibles para este vehículo
                </div>
            `);
      this.$(".wsale_products_categories_list").after(message);
    }
  },

  /**
   * Mostrar información del filtro aplicado
   * @private
   * @param {number} totalCategories - Total de categorías mostradas
   * @param {boolean} hasFilter - Si hay filtro activo
   */
  _showFilterInfo: function (totalCategories, hasFilter) {
    this._hideFilterInfo(); // Limpiar mensaje anterior

    if (hasFilter && totalCategories > 0) {
      const message = $(`
                <div class="category-filter-info alert alert-success text-center mt-2">
                    <i class="fa fa-filter"></i>
                    Mostrando ${totalCategories} categorías compatibles con tu vehículo
                </div>
            `);
      this.$(".wsale_products_categories_list").after(message);
    }
  },

  /**
   * Ocultar información del filtro
   * @private
   */
  _hideFilterInfo: function () {
    this.$(".category-filter-info, .no-categories-message").remove();
  },
});

export default publicWidget.registry.CategoryVehicleFilter;
