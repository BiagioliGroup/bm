/**
 * 🚀 JAVASCRIPT PARA CATEGORÍAS PERSONALIZADAS DE MOTOS
 * Maneja la funcionalidad de expandir/contraer categorías
 * y mejora la experiencia del usuario
 */

odoo.define("sh_motorcycle_frontend.categories", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");
  var core = require("web.core");

  // Widget principal para manejar las categorías
  publicWidget.registry.MotorcycleCategoriesWidget = publicWidget.Widget.extend(
    {
      selector: ".motorcycle_categories_container",
      events: {
        "click .motorcycle_category_header": "_onCategoryClick",
        "click .motorcycle_category_icon": "_onIconClick",
      },

      /**
       * Inicialización del widget
       */
      start: function () {
        this._super.apply(this, arguments);
        this._initializeCategories();
        return this._super.apply(this, arguments);
      },

      /**
       * Inicializa el estado de las categorías
       */
      _initializeCategories: function () {
        var self = this;

        // Marcar categorías activas y expandir sus padres
        this.$(".motorcycle_category_header.active").each(function () {
          self._expandParentCategories($(this));
        });

        // Precargar conteos de productos si están disponibles
        this._loadProductCounts();
      },

      /**
       * Maneja el click en el header de una categoría
       */
      _onCategoryClick: function (ev) {
        ev.preventDefault();
        var $header = $(ev.currentTarget);
        var $categoryItem = $header.closest(".motorcycle_category_item");
        var $subcategories = $categoryItem.find("> .motorcycle_subcategories");

        // Solo expandir/contraer si tiene subcategorías
        if ($subcategories.length > 0) {
          this._toggleCategory($categoryItem);
        } else {
          // Si no tiene subcategorías, seguir el enlace
          var href = $header.find(".motorcycle_category_link").attr("href");
          if (href) {
            window.location.href = href;
          }
        }
      },

      /**
       * Maneja el click específico en el icono
       */
      _onIconClick: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();

        var $icon = $(ev.currentTarget);
        var $categoryItem = $icon.closest(".motorcycle_category_item");

        this._toggleCategory($categoryItem);
      },

      /**
       * Expande o contrae una categoría
       */
      _toggleCategory: function ($categoryItem) {
        var $subcategories = $categoryItem.find("> .motorcycle_subcategories");
        var $icon = $categoryItem.find(
          "> .motorcycle_category_header .motorcycle_category_icon"
        );

        if ($subcategories.hasClass("show")) {
          // Contraer
          $subcategories.removeClass("show").addClass("collapse");
          $icon.removeClass("fa-minus").addClass("fa-plus");
          this._animateCollapse($subcategories);
        } else {
          // Expandir
          $subcategories.removeClass("collapse").addClass("show");
          $icon.removeClass("fa-plus").addClass("fa-minus");
          this._animateExpand($subcategories);
        }
      },

      /**
       * Animación para expandir categoría
       */
      _animateExpand: function ($element) {
        $element.css("max-height", "0px").animate(
          {
            "max-height": "1000px",
          },
          300
        );
      },

      /**
       * Animación para contraer categoría
       */
      _animateCollapse: function ($element) {
        $element.animate(
          {
            "max-height": "0px",
          },
          300
        );
      },

      /**
       * Expande las categorías padre de una categoría activa
       */
      _expandParentCategories: function ($activeHeader) {
        var $parentSubcategories = $activeHeader.closest(
          ".motorcycle_subcategories"
        );

        while ($parentSubcategories.length > 0) {
          var $parentItem = $parentSubcategories.closest(
            ".motorcycle_category_item"
          );

          // Expandir categoría padre
          $parentSubcategories.removeClass("collapse").addClass("show");
          $parentItem
            .find("> .motorcycle_category_header .motorcycle_category_icon")
            .removeClass("fa-plus")
            .addClass("fa-minus");

          // Buscar el siguiente nivel padre
          $parentSubcategories = $parentItem.parent(
            ".motorcycle_subcategories"
          );
        }
      },

      /**
       * Carga dinámicamente los conteos de productos
       */
      _loadProductCounts: function () {
        // Esta función puede ser extendida para cargar conteos via AJAX
        // si se necesita actualización dinámica
        console.log("🔢 Product counts loaded");
      },
    }
  );

  // Widget para mejorar la experiencia en móviles
  publicWidget.registry.MotorcycleCategoriesMobile = publicWidget.Widget.extend(
    {
      selector: ".motorcycle_categories_container",
      events: {
        "touchstart .motorcycle_category_header": "_onTouchStart",
        "touchend .motorcycle_category_header": "_onTouchEnd",
      },

      /**
       * Manejo táctil para móviles
       */
      _onTouchStart: function (ev) {
        $(ev.currentTarget).addClass("touching");
      },

      _onTouchEnd: function (ev) {
        var $target = $(ev.currentTarget);
        setTimeout(function () {
          $target.removeClass("touching");
        }, 150);
      },
    }
  );

  // Utilidades adicionales para categorías
  var MotorcycleCategoriesUtils = {
    /**
     * Obtiene la categoría activa actual
     */
    getCurrentCategory: function () {
      return $(".motorcycle_category_header.active").first();
    },

    /**
     * Navega a una categoría específica
     */
    navigateToCategory: function (categoryId) {
      var $categoryLink = $(
        `.motorcycle_category_item[data-category-id="${categoryId}"] .motorcycle_category_link`
      );
      if ($categoryLink.length > 0) {
        window.location.href = $categoryLink.attr("href");
      }
    },

    /**
     * Filtra categorías por nombre
     */
    filterCategories: function (searchTerm) {
      var $container = $(".motorcycle_categories_container");

      if (!searchTerm) {
        $container.find(".motorcycle_category_item").show();
        return;
      }

      $container.find(".motorcycle_category_item").each(function () {
        var $item = $(this);
        var categoryName = $item
          .find(".motorcycle_category_link span")
          .text()
          .toLowerCase();

        if (categoryName.includes(searchTerm.toLowerCase())) {
          $item.show();
        } else {
          $item.hide();
        }
      });
    },
  };

  // Exponemos las utilidades globalmente para uso desde otros módulos
  core.motorcycle_categories_utils = MotorcycleCategoriesUtils;

  return {
    MotorcycleCategoriesWidget:
      publicWidget.registry.MotorcycleCategoriesWidget,
    MotorcycleCategoriesMobile:
      publicWidget.registry.MotorcycleCategoriesMobile,
    Utils: MotorcycleCategoriesUtils,
  };
});

/**
 * 🎯 INICIALIZACIÓN AUTOMÁTICA
 * Se ejecuta cuando el DOM está listo
 */
$(document).ready(function () {
  console.log("🏍️  Motorcycle Categories System Initialized");

  // Aplicar efectos adicionales si es necesario
  if ($(".motorcycle_categories_container").length > 0) {
    console.log("✅ Categories container found and ready");

    // Mejorar accesibilidad
    $(".motorcycle_category_header")
      .attr("role", "button")
      .attr("tabindex", "0")
      .on("keypress", function (e) {
        if (e.which === 13 || e.which === 32) {
          // Enter o Espacio
          $(this).click();
        }
      });
  }
});
