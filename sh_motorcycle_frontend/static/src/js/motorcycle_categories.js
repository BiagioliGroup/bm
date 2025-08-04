/**
 * 🚀 JAVASCRIPT PARA CATEGORÍAS PERSONALIZADAS DE MOTOS
 * Maneja iconos y funcionalidad expand/collapse
 */

odoo.define("sh_motorcycle_frontend.categories", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");

  // Widget principal para manejar las categorías
  publicWidget.registry.MotorcycleCategoriesWidget = publicWidget.Widget.extend(
    {
      selector: ".motorcycle_categories_container",

      /**
       * Inicialización del widget
       */
      start: function () {
        console.log("🏍️ Inicializando categorías de motos...");
        this._addCategoryIcons();
        this._expandActiveCategory();
        this._addKeyboardSupport();
        return this._super.apply(this, arguments);
      },

      /**
       * Agregar iconos a las categorías
       */
      _addCategoryIcons: function () {
        var self = this;

        // Agregar iconos a categorías que tienen subcategorías
        this.$(".motorcycle_categories_list .nav-item").each(function () {
          var $item = $(this);
          var $link = $item.find("> a");
          var $subcategoryList = $item.find("ul.motorcycle_subcategories");

          if ($link.length && $subcategoryList.length) {
            // Categoría con subcategorías - agregar icono expandible
            var $icon = $(
              '<i class="motorcycle_category_icon fa fa-plus me-2"></i>'
            );
            $icon.css({
              cursor: "pointer",
              width: "16px",
              "text-align": "center",
            });

            // Evento click para expandir/contraer
            $icon.on("click", function (e) {
              e.preventDefault();
              e.stopPropagation();
              self._toggleSubcategory($subcategoryList, $icon);
            });

            // Insertar icono al inicio del link
            $link.prepend($icon);

            // Ocultar subcategorías por defecto
            $subcategoryList.hide();
          } else if ($link.length) {
            // Categoría sin subcategorías - agregar icono de carpeta
            var $icon = $(
              '<i class="motorcycle_category_icon fa fa-folder-o me-2"></i>'
            );
            $icon.css({
              width: "16px",
              "text-align": "center",
            });
            $link.prepend($icon);
          }
        });
      },

      /**
       * Alternar subcategoría (expandir/contraer)
       */
      _toggleSubcategory: function ($subcategoryList, $icon) {
        if ($subcategoryList.is(":visible")) {
          $subcategoryList.slideUp(300);
          $icon.removeClass("fa-minus").addClass("fa-plus");
        } else {
          $subcategoryList.slideDown(300);
          $icon.removeClass("fa-plus").addClass("fa-minus");
        }
      },

      /**
       * Auto-expandir categoría activa
       */
      _expandActiveCategory: function () {
        var currentPath = window.location.pathname;
        var self = this;

        this.$(".motorcycle_categories_list a").each(function () {
          var $link = $(this);
          if ($link.attr("href") === currentPath) {
            $link.addClass("active");

            // Expandir categorías padre si es una subcategoría
            var $parentUl = $link.closest("ul.motorcycle_subcategories");
            while ($parentUl.length > 0) {
              $parentUl.show();
              var $parentIcon = $parentUl
                .parent()
                .find("> a .motorcycle_category_icon");
              if ($parentIcon.hasClass("fa-plus")) {
                $parentIcon.removeClass("fa-plus").addClass("fa-minus");
              }
              $parentUl = $parentUl
                .parent()
                .closest("ul.motorcycle_subcategories");
            }
          }
        });
      },

      /**
       * Agregar soporte de teclado para accesibilidad
       */
      _addKeyboardSupport: function () {
        this.$(".motorcycle_category_icon")
          .attr("role", "button")
          .attr("tabindex", "0")
          .on("keypress", function (e) {
            if (e.which === 13 || e.which === 32) {
              // Enter o Espacio
              e.preventDefault();
              $(this).click();
            }
          });
      },
    }
  );

  return {
    MotorcycleCategoriesWidget:
      publicWidget.registry.MotorcycleCategoriesWidget,
  };
});

/**
 * 🎯 INICIALIZACIÓN ADICIONAL
 * Para funcionalidad que no depende del widget
 */
$(document).ready(function () {
  console.log("🏍️ Sistema de categorías de motos listo");

  // Funcionalidad adicional si es necesaria
  // Por ejemplo, detectar cambios en filtros de motocicletas
  $(".motorcycle_categories_container").on("category_update", function () {
    console.log("📝 Categorías actualizadas");
  });
});
