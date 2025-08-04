/** @odoo-module */

/**
 * 🏍️ CATEGORÍAS DE MOTOS - VERSIÓN COMPATIBLE CON SEARCH.JS
 * Optimizado para no interferir con la funcionalidad de búsqueda
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MotorcycleCategoriesEnhancer = publicWidget.Widget.extend(
  {
    selector: ".products_categories:not(#wrap)", // Evitar conflicto con search.js que usa #wrap
    events: {
      "click .nav-item.has-subcategories > a": "_onCategoryClick",
      "keydown .nav-item.has-subcategories > a": "_onCategoryKeydown",
    },

    /**
     * @override
     */
    start: function () {
      console.log("🏍️ Inicializando categorías de motos...");
      this._initializeCategories();
      this._markActiveCategory();
      return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Inicializar la estructura de categorías
     * @private
     */
    _initializeCategories: function () {
      // Identificar categorías con subcategorías
      this.$(".nav-item").each((index, element) => {
        const $item = $(element);
        const $subcategories = $item.find(".nav-hierarchy");

        if ($subcategories.length > 0) {
          $item.addClass("has-subcategories");
          $subcategories.hide(); // Ocultar por defecto
        }
      });
    },

    /**
     * Marcar la categoría activa basada en la URL actual
     * @private
     */
    _markActiveCategory: function () {
      const currentPath = window.location.pathname;

      this.$("a[href]").each((index, element) => {
        const $link = $(element);
        const href = $link.attr("href");

        if (href === currentPath) {
          $link.addClass("active-category");

          // Auto-expandir categorías padre si es una subcategoría
          const $parentHierarchy = $link.closest(".nav-hierarchy");
          if ($parentHierarchy.length > 0) {
            $parentHierarchy.show();
            $parentHierarchy.parent().addClass("expanded");
          }
        }
      });
    },

    /**
     * Alternar visibilidad de subcategorías
     * @private
     * @param {jQuery} $item - Item de categoría
     * @param {jQuery} $subcategories - Elemento de subcategorías
     */
    _toggleSubcategories: function ($item, $subcategories) {
      if ($subcategories.is(":visible")) {
        $subcategories.slideUp(200);
        $item.removeClass("expanded");
      } else {
        // Cerrar otras categorías abiertas primero
        this.$(".nav-item.expanded")
          .not($item)
          .each((index, element) => {
            const $otherItem = $(element);
            $otherItem.find(".nav-hierarchy").slideUp(200);
            $otherItem.removeClass("expanded");
          });

        $subcategories.slideDown(200);
        $item.addClass("expanded");
      }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Manejar click en categorías con subcategorías
     * @private
     * @param {Event} ev
     */
    _onCategoryClick: function (ev) {
      ev.preventDefault();
      const $item = $(ev.currentTarget).parent();
      const $subcategories = $item.find(".nav-hierarchy");

      if ($subcategories.length > 0) {
        this._toggleSubcategories($item, $subcategories);
      }
    },

    /**
     * Manejar navegación por teclado
     * @private
     * @param {Event} ev
     */
    _onCategoryKeydown: function (ev) {
      if (ev.which === 13 || ev.which === 32) {
        // Enter o Espacio
        ev.preventDefault();
        this._onCategoryClick(ev);
      }
    },
  }
);

/**
 * Widget adicional para efectos sutiles en las categorías
 * Selector específico para evitar conflictos con el buscador de vehículos
 */
publicWidget.registry.MotorcycleCategoriesEffects = publicWidget.Widget.extend({
  selector: '.products_categories a[href^="/shop/category/"]:not(#wrap a)', // Evitar conflicto
  events: {
    click: "_onCategoryLinkClick",
  },

  /**
   * Agregar efecto visual sutil al hacer click en enlaces de categoría
   * @private
   * @param {Event} ev
   */
  _onCategoryLinkClick: function (ev) {
    const $link = $(ev.currentTarget);

    // Efecto visual sutil
    $link.css("opacity", "0.7");
    setTimeout(() => {
      $link.css("opacity", "1");
    }, 150);
  },
});

export default {
  MotorcycleCategoriesEnhancer:
    publicWidget.registry.MotorcycleCategoriesEnhancer,
  MotorcycleCategoriesEffects:
    publicWidget.registry.MotorcycleCategoriesEffects,
};
