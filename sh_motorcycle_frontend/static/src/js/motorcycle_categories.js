/**
 * 🚀 JAVASCRIPT PARA CATEGORÍAS DE MOTOS - SIN TEMPLATES
 * Solo mejora la funcionalidad del HTML existente
 */

odoo.define("sh_motorcycle_frontend.categories_enhance", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");

  // Widget para mejorar las categorías existentes
  publicWidget.registry.MotorcycleCategoriesEnhancer =
    publicWidget.Widget.extend({
      selector: ".products_categories",

      /**
       * Inicialización del widget
       */
      start: function () {
        console.log("🏍️ Inicializando mejoras de categorías...");
        this._enhanceCategories();
        this._addClickToExpand();
        this._markActiveCategory();
        this._addKeyboardNavigation();
        return this._super.apply(this, arguments);
      },

      /**
       * Mejora las categorías existentes con funcionalidad adicional
       */
      _enhanceCategories: function () {
        var self = this;

        // Agregar funcionalidad de expand/collapse con click
        this.$(".nav-item").each(function () {
          var $item = $(this);
          var $link = $item.find("> a");
          var $subcategories = $item.find(".nav-hierarchy");

          if ($subcategories.length > 0) {
            // Agregar clase para identificar categorías expandibles
            $item.addClass("has-subcategories");

            // Ocultar subcategorías inicialmente
            $subcategories.hide();

            // Cambiar el cursor
            $link.css("cursor", "pointer");
          }
        });

        console.log("✅ Categorías mejoradas");
      },

      /**
       * Agregar funcionalidad de click para expandir/contraer
       */
      _addClickToExpand: function () {
        var self = this;

        this.$(".has-subcategories > a").on("click", function (e) {
          // Solo prevenir si es una categoría con subcategorías
          var $link = $(this);
          var $item = $link.parent();
          var $subcategories = $item.find(".nav-hierarchy");

          if ($subcategories.length > 0) {
            e.preventDefault();
            self._toggleSubcategories($item, $subcategories);
          }
          // Si no tiene subcategorías, permitir navegación normal
        });
      },

      /**
       * Alternar subcategorías
       */
      _toggleSubcategories: function ($item, $subcategories) {
        if ($subcategories.is(":visible")) {
          // Contraer con animación
          $subcategories.slideUp(300);
          $item.removeClass("expanded");
        } else {
          // Expandir con animación
          $subcategories.slideDown(300);
          $item.addClass("expanded");

          // Contraer otras categorías abiertas (opcional)
          this.$(".has-subcategories")
            .not($item)
            .each(function () {
              var $otherSub = $(this).find(".nav-hierarchy");
              if ($otherSub.is(":visible")) {
                $otherSub.slideUp(200);
                $(this).removeClass("expanded");
              }
            });
        }
      },

      /**
       * Marcar la categoría activa basada en la URL
       */
      _markActiveCategory: function () {
        var currentPath = window.location.pathname;
        var self = this;

        this.$("a[href]").each(function () {
          var $link = $(this);
          var href = $link.attr("href");

          if (href === currentPath) {
            $link.addClass("active-category");

            // Auto-expandir categorías padre
            var $parentHierarchy = $link.closest(".nav-hierarchy");
            while ($parentHierarchy.length > 0) {
              $parentHierarchy.show();
              $parentHierarchy.parent().addClass("expanded");
              $parentHierarchy = $parentHierarchy
                .parent()
                .closest(".nav-hierarchy");
            }
          }
        });
      },

      /**
       * Agregar navegación por teclado
       */
      _addKeyboardNavigation: function () {
        this.$(".has-subcategories > a").attr("tabindex", "0");

        this.$(".has-subcategories > a").on("keydown", function (e) {
          if (e.which === 13 || e.which === 32) {
            // Enter o Espacio
            e.preventDefault();
            $(this).click();
          }
        });
      },

      /**
       * Función pública para contraer todas las categorías
       */
      collapseAll: function () {
        this.$(".nav-hierarchy").slideUp(200);
        this.$(".has-subcategories").removeClass("expanded");
      },

      /**
       * Función pública para expandir todas las categorías
       */
      expandAll: function () {
        this.$(".nav-hierarchy").slideDown(300);
        this.$(".has-subcategories").addClass("expanded");
      },
    });

  return {
    MotorcycleCategoriesEnhancer:
      publicWidget.registry.MotorcycleCategoriesEnhancer,
  };
});

/**
 * 🎯 FUNCIONALIDAD ADICIONAL SIN WIDGETS
 * Se ejecuta cuando el DOM está listo
 */
$(document).ready(function () {
  console.log("🏍️ Sistema de categorías mejorado cargado");

  // Agregar indicadores visuales adicionales
  setTimeout(function () {
    // Agregar badges con número de subcategorías
    $(".products_categories .nav-item").each(function () {
      var $item = $(this);
      var $subcategories = $item.find(".nav-hierarchy .nav-item");

      if ($subcategories.length > 0) {
        var $badge = $(
          '<span class="category-count badge badge-secondary ms-2"></span>'
        );
        $badge.text($subcategories.length);
        $badge.css({
          "font-size": "10px",
          "background-color": "#6c757d",
          color: "white",
          padding: "2px 6px",
          "border-radius": "10px",
          "margin-left": "8px",
        });
        $item.find("> a").append($badge);
      }
    });

    console.log("✅ Badges de conteo agregados");
  }, 500);

  // Funcionalidad de búsqueda en categorías (opcional)
  if ($(".products_categories").length > 0) {
    // Agregar campo de búsqueda
    var $searchContainer = $('<div class="category-search mb-3"></div>');
    var $searchInput = $(
      '<input type="text" class="form-control form-control-sm" placeholder="Buscar categorías...">'
    );

    $searchContainer.append($searchInput);
    $(".products_categories .o_categories_collapse_title").after(
      $searchContainer
    );

    // Funcionalidad de búsqueda
    $searchInput.on("input", function () {
      var searchTerm = $(this).val().toLowerCase();

      if (searchTerm === "") {
        // Mostrar todas las categorías
        $(".products_categories .nav-item").show();
      } else {
        // Filtrar categorías
        $(".products_categories .nav-item").each(function () {
          var $item = $(this);
          var categoryText = $item.find("> a").text().toLowerCase();

          if (categoryText.includes(searchTerm)) {
            $item.show();
          } else {
            $item.hide();
          }
        });
      }
    });

    console.log("✅ Buscador de categorías agregado");
  }

  // Agregar efecto de scroll suave
  $('.products_categories a[href^="/shop/category/"]').on(
    "click",
    function (e) {
      // No prevenir la navegación, solo agregar efecto visual
      $(this).addClass("clicked");
      setTimeout(function () {
        $(".products_categories a").removeClass("clicked");
      }, 200);
    }
  );
});

/**
 * 🔧 UTILIDADES GLOBALES
 */
window.MotorcycleCategories = {
  /**
   * Función para colapsar todas las categorías
   */
  collapseAll: function () {
    $(".products_categories .nav-hierarchy").slideUp(200);
    $(".products_categories .has-subcategories").removeClass("expanded");
  },

  /**
   * Función para expandir todas las categorías
   */
  expandAll: function () {
    $(".products_categories .nav-hierarchy").slideDown(300);
    $(".products_categories .has-subcategories").addClass("expanded");
  },

  /**
   * Función para buscar categorías
   */
  searchCategories: function (term) {
    $(".category-search input").val(term).trigger("input");
  },
};
