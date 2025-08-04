/** @odoo-module */

/**
 * 🏍️ WIDGET UNIFICADO: Categorías + Filtrado por Vehículo
 * Combina toda la funcionalidad en un solo widget para evitar conflictos
 */

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.UnifiedCategoryWidget = publicWidget.Widget.extend({
  selector: ".products_categories",
  events: {
    "click .nav-item.has-subcategories > a": "_onCategoryClick",
    "keydown .nav-item.has-subcategories > a": "_onCategoryKeydown",
    "click a[href^='/shop/category/']": "_onCategoryLinkClick",
  },

  /**
   * @override
   */
  start: function () {
    console.log("🏍️ Inicializando widget unificado de categorías...");

    // 1. Funcionalidades de categorías (tu código original)
    this._initializeCategories();
    this._markActiveCategory();

    // 2. Funcionalidad de filtrado por vehículo
    this._setupVehicleFiltering();

    return this._super.apply(this, arguments);
  },

  //--------------------------------------------------------------------------
  // Funcionalidades de Categorías (Tu código original)
  //--------------------------------------------------------------------------

  _initializeCategories: function () {
    this.$(".nav-item").each((index, element) => {
      const $item = $(element);
      const $subcategories = $item.find(".nav-hierarchy");

      if ($subcategories.length > 0) {
        $item.addClass("has-subcategories");
      }
    });
  },

  _markActiveCategory: function () {
    const currentPath = window.location.pathname;

    this.$("a[href]").each((index, element) => {
      const $link = $(element);
      const href = $link.attr("href");

      if (href === currentPath) {
        $link.addClass("active-category");
        const $parentHierarchy = $link.closest(".nav-hierarchy");
        if ($parentHierarchy.length > 0) {
          $parentHierarchy.show();
          $parentHierarchy.parent().addClass("expanded");
        }
      }
    });
  },

  _toggleSubcategories: function ($item, $subcategories) {
    if ($item.hasClass("expanded")) {
      $item.removeClass("expanded");
    } else {
      $item.addClass("expanded");
    }
  },

  //--------------------------------------------------------------------------
  // Funcionalidades de Filtrado por Vehículo (Nueva)
  //--------------------------------------------------------------------------

  _setupVehicleFiltering: function () {
    console.log("🔍 Configurando filtrado por vehículo...");

    // Escuchar cambios en selectores de vehículo
    this._setupVehicleChangeListeners();

    // Aplicar filtro inicial si hay vehículo en URL
    this._applyInitialFilter();
  },

  _setupVehicleChangeListeners: function () {
    const self = this;

    $(document).on(
      "change",
      'select[name="type"], select[name="make"], select[name="model"], select[name="year"]',
      function () {
        console.log("🔄 Cambio detectado en selector de vehículo");
        setTimeout(() => {
          self._updateCategoriesBasedOnVehicle();
        }, 500); // Dar tiempo a que search.js termine
      }
    );
  },

  _applyInitialFilter: function () {
    const urlParams = new URLSearchParams(window.location.search);
    const hasVehicleParams =
      urlParams.get("type") &&
      urlParams.get("make") &&
      urlParams.get("model") &&
      urlParams.get("year");

    if (hasVehicleParams) {
      console.log("🎯 Aplicando filtro inicial por vehículo en URL");
      setTimeout(() => {
        this._updateCategoriesBasedOnVehicle();
      }, 1000); // Dar tiempo a que la página cargue completamente
    }
  },

  _getCurrentVehicleSelection: function () {
    // Intentar de selectores primero
    let vehicleData = {
      type: $('select[name="type"]').val() || "",
      make: $('select[name="make"]').val() || "",
      model: $('select[name="model"]').val() || "",
      year: $('select[name="year"]').val() || "",
    };

    // Si no hay selectores, obtener de URL
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

  _isVehicleComplete: function (vehicleData) {
    return (
      vehicleData.type &&
      vehicleData.make &&
      vehicleData.model &&
      vehicleData.year
    );
  },

  _updateCategoriesBasedOnVehicle: function () {
    const vehicleData = this._getCurrentVehicleSelection();

    console.log("🔍 Actualizando categorías para vehículo:", vehicleData);

    if (!this._isVehicleComplete(vehicleData)) {
      console.log("🔍 Vehículo incompleto, mostrando todas las categorías");
      this._showAllCategories();
      return;
    }

    // Llamar API para obtener categorías filtradas
    rpc("/shop/categories/filtered", vehicleData)
      .then((result) => {
        console.log("🔍 Respuesta de API de categorías:", result);
        this._applyFilter(result);
      })
      .catch((error) => {
        console.error("❌ Error al filtrar categorías:", error);
        this._showAllCategories(); // Fallback
      });
  },

  _applyFilter: function (result) {
    if (!result.categories || result.categories.length === 0) {
      console.log("🔍 No hay categorías para este vehículo");
      this._hideAllCategories();
      this._showNoCategories();
      return;
    }

    // Recopilar IDs permitidos
    const allowedIds = new Set();
    const collectIds = (categories) => {
      categories.forEach((category) => {
        allowedIds.add(category.id);
        if (category.children && category.children.length > 0) {
          collectIds(category.children);
        }
      });
    };
    collectIds(result.categories);

    console.log("🔍 IDs de categorías permitidas:", Array.from(allowedIds));

    // Filtrar categorías visualmente
    this._filterCategoriesVisually(allowedIds);

    // Mostrar mensaje informativo
    this._showFilterInfo(result.total_categories);
  },

  _filterCategoriesVisually: function (allowedIds) {
    let hiddenCount = 0;
    let shownCount = 0;

    this.$(".nav-item").each((index, element) => {
      const $item = $(element);
      const $link = $item.find('> a[href*="/shop/category/"]');

      if ($link.length > 0) {
        const href = $link.attr("href");
        const categoryId = this._extractCategoryIdFromUrl(href);

        if (categoryId && allowedIds.has(categoryId)) {
          // Mostrar categoría - SIN interferir con tus animaciones CSS
          $item
            .removeClass("d-none category-filtered-hidden")
            .addClass("category-filtered-visible");
          shownCount++;
        } else {
          // Ocultar categoría - SIN interferir con tus animaciones CSS
          $item
            .removeClass("category-filtered-visible")
            .addClass("d-none category-filtered-hidden");
          hiddenCount++;
        }
      }
    });

    console.log(
      `🔍 Categorías mostradas: ${shownCount}, ocultas: ${hiddenCount}`
    );
  },

  _extractCategoryIdFromUrl: function (url) {
    if (!url) return null;
    const match = url.match(/\/shop\/category\/.*-(\d+)$/);
    return match ? parseInt(match[1]) : null;
  },

  _showAllCategories: function () {
    console.log("🔍 Mostrando todas las categorías");
    this.$(".nav-item").removeClass(
      "d-none category-filtered-hidden category-filtered-visible"
    );
    this._hideMessages();
  },

  _hideAllCategories: function () {
    this.$(".nav-item")
      .addClass("d-none category-filtered-hidden")
      .removeClass("category-filtered-visible");
  },

  _showNoCategories: function () {
    if (this.$(".no-categories-message").length === 0) {
      const message = $(`
                <div class="no-categories-message alert alert-warning text-center mt-3">
                    <i class="fa fa-exclamation-triangle"></i>
                    No hay categorías disponibles para este vehículo
                </div>
            `);
      this.$el.after(message);
    }
  },

  _showFilterInfo: function (totalCategories) {
    this._hideMessages();

    if (totalCategories > 0) {
      const message = $(`
                <div class="category-filter-info alert alert-success text-center mt-2">
                    <i class="fa fa-filter"></i>
                    Mostrando ${totalCategories} categorías compatibles con tu vehículo
                </div>
            `);
      this.$el.after(message);
    }
  },

  _hideMessages: function () {
    $(".category-filter-info, .no-categories-message").remove();
  },

  //--------------------------------------------------------------------------
  // Handlers (Combinados)
  //--------------------------------------------------------------------------

  _onCategoryClick: function (ev) {
    ev.preventDefault();
    const $item = $(ev.currentTarget).parent();
    const $subcategories = $item.find(".nav-hierarchy");

    if ($subcategories.length > 0) {
      this._toggleSubcategories($item, $subcategories);
    }
  },

  _onCategoryKeydown: function (ev) {
    if (ev.which === 13 || ev.which === 32) {
      ev.preventDefault();
      this._onCategoryClick(ev);
    }
  },

  _onCategoryLinkClick: function (ev) {
    // Efecto visual sutil (tu código original)
    const $link = $(ev.currentTarget);
    $link.css("opacity", "0.7");
    setTimeout(() => {
      $link.css("opacity", "1");
    }, 150);
  },
});

// Función global para testing
window.debugCategoryFilter = {
  test: function () {
    const widget = $(".products_categories").data("widget");
    if (widget && widget._updateCategoriesBasedOnVehicle) {
      widget._updateCategoriesBasedOnVehicle();
    } else {
      console.error("Widget no encontrado");
    }
  },
};

console.log("🏍️ Widget unificado de categorías cargado");

export default publicWidget.registry.UnifiedCategoryWidget;
