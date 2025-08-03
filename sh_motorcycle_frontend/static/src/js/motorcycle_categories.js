/**
 * 🚀 JAVASCRIPT SIMPLE PARA CATEGORÍAS PERSONALIZADAS DE MOTOS
 * Solo maneja la funcionalidad básica de expand/collapse
 */

odoo.define("sh_motorcycle_frontend.categories", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");

  // Widget simple para manejar las categorías
  publicWidget.registry.MotorcycleCategoriesWidget = publicWidget.Widget.extend(
    {
      selector: ".motorcycle_categories_container",
      events: {
        "click .motorcycle_category_icon": "_onIconClick",
      },

      /**
       * Inicialización del widget
       */
      start: function () {
        this._initializeCategories();
        return this._super.apply(this, arguments);
      },

      /**
       * Inicializa el estado de las categorías
       */
      _initializeCategories: function () {
        // Auto-expandir categoría activa
        this._expandActiveCategory();

        console.log("🏍️ Motorcycle Categories initialized");
      },

      /**
       * Maneja el click en el icono
       */
      _onIconClick: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();

        var $icon = $(ev.currentTarget);
        var $categoryItem = $icon.closest(".motorcycle_category_item");
        var $subcategories = $categoryItem.find("> .motorcycle_subcategories");

        if ($subcategories.length > 0) {
          this._toggleCategory($subcategories, $icon);
        }
      },

      /**
       * Expande o contrae una categoría
       */
      _toggleCategory: function ($subcategories, $icon) {
        if ($subcategories.is(":visible")) {
          // Contraer
          $subcategories.slideUp(300);
          $icon.removeClass("fa-minus").addClass("fa-plus");
        } else {
          // Expandir
          $subcategories.slideDown(300);
          $icon.removeClass("fa-plus").addClass("fa-minus");
        }
      },

      /**
       * Expande automáticamente la categoría activa
       */
      _expandActiveCategory: function () {
        var $activeLink = this.$(
          'a[href*="' + window.location.pathname + '"]'
        ).first();
        if ($activeLink.length > 0) {
          $activeLink.addClass("active");

          // Expandir categorías padre
          var $parentSubcategories = $activeLink.closest(
            ".motorcycle_subcategories"
          );
          while ($parentSubcategories.length > 0) {
            $parentSubcategories.show();
            var $parentIcon = $parentSubcategories
              .siblings("a")
              .find(".motorcycle_category_icon");
            $parentIcon.removeClass("fa-plus").addClass("fa-minus");

            $parentSubcategories = $parentSubcategories
              .parent()
              .closest(".motorcycle_subcategories");
          }
        }
      },
    }
  );

  return {
    MotorcycleCategoriesWidget:
      publicWidget.registry.MotorcycleCategoriesWidget,
  };
});

/**
 * 🎯 INICIALIZACIÓN AUTOMÁTICA
 * Se ejecuta cuando el DOM está listo
 */
$(document).ready(function () {
  console.log("🏍️ Motorcycle Categories System Ready");

  // Mejorar accesibilidad
  $(".motorcycle_category_icon")
    .attr("role", "button")
    .attr("tabindex", "0")
    .on("keypress", function (e) {
      if (e.which === 13 || e.which === 32) {
        // Enter o Espacio
        $(this).click();
      }
    });
});
