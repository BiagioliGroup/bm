/**
 * 🚀 JAVASCRIPT PARA CATEGORÍAS DE MOTOS - SIN TEMPLATES
 * Solo mejora la funcionalidad del HTML existente
 */

odoo.define('sh_motorcycle_frontend.categories_enhance', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    // Widget para mejorar las categorías existentes
    publicWidget.registry.MotorcycleCategoriesEnhancer = publicWidget.Widget.extend({
        selector: '.products_categories',
        
        /**
         * Inicialización del widget
         */
        start: function () {
            console.log('🏍️ Inicializando mejoras de categorías...');
            this._enhanceCategories();
            this._addClickToExpand();
            this._markActiveCategory();
            this._addKeyboardNavigation();
            return this._super.apply(this, arguments);
        },

/**
 * 🚀 JAVASCRIPT SUTIL PARA CATEGORÍAS DE MOTOS
 * Funcionalidad mínima sin efectos exagerados
 */

odoo.define('sh_motorcycle_frontend.categories_subtle', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    // Widget minimalista para categorías
    publicWidget.registry.MotorcycleCategoriesSubtle = publicWidget.Widget.extend({
        selector: '.products_categories',
        
        /**
         * Inicialización del widget
         */
        start: function () {
            console.log('🏍️ Categorías sutiles inicializadas...');
            this._addClickToExpand();
            this._markActiveCategory();
            return this._super.apply(this, arguments);
        },

        /**
         * Agregar funcionalidad de click para expandir/contraer
         */
        _addClickToExpand: function () {
            var self = this;
            
            // Solo para categorías que tienen subcategorías
            this.$('.nav-item').each(function() {
                var $item = $(this);
                var $link = $item.find('> a');
                var $subcategories = $item.find('.nav-hierarchy');
                
                if ($subcategories.length > 0) {
                    $item.addClass('has-subcategories');
                    $subcategories.hide(); // Ocultar por defecto
                    
                    $link.on('click', function(e) {
                        e.preventDefault();
                        self._toggleSubcategories($item, $subcategories);
                    });
                }
            });
        },

        /**
         * Alternar subcategorías - SIN ANIMACIONES COMPLEJAS
         */
        _toggleSubcategories: function ($item, $subcategories) {
            if ($subcategories.is(':visible')) {
                $subcategories.slideUp(200); // Más rápido
                $item.removeClass('expanded');
            } else {
                $subcategories.slideDown(200); // Más rápido
                $item.addClass('expanded');
            }
        },

        /**
         * Marcar la categoría activa
         */
        _markActiveCategory: function () {
            var currentPath = window.location.pathname;
            
            this.$('a[href]').each(function() {
                var $link = $(this);
                var href = $link.attr('href');
                
                if (href === currentPath) {
                    $link.addClass('active-category');
                    
                    // Auto-expandir categorías padre
                    var $parentHierarchy = $link.closest('.nav-hierarchy');
                    if ($parentHierarchy.length > 0) {
                        $parentHierarchy.show();
                        $parentHierarchy.parent().addClass('expanded');
                    }
                }
            });
        }
    });

    return {
        MotorcycleCategoriesSubtle: publicWidget.registry.MotorcycleCategoriesSubtle
    };
});

/**
 * 🎯 FUNCIONALIDAD MÍNIMA
 */
$(document).ready(function () {
    console.log('🏍️ Sistema sutil de categorías cargado');
    
    // Solo agregar navegación por teclado básica
    $('.products_categories .has-subcategories > a').on('keydown', function(e) {
        if (e.which === 13 || e.which === 32) { // Enter o Espacio
            e.preventDefault();
            $(this).click();
        }
    });
});
    });

    return {
        MotorcycleCategoriesEnhancer: publicWidget.registry.MotorcycleCategoriesEnhancer
    };
});

/**
 * 🎯 FUNCIONALIDAD MÍNIMA Y SUTIL
 */
$(document).ready(function () {
    console.log('🏍️ Sistema sutil de categorías cargado');
    
    // Solo agregar navegación por teclado básica
    $('.products_categories .has-subcategories > a').on('keydown', function(e) {
        if (e.which === 13 || e.which === 32) { // Enter o Espacio
            e.preventDefault();
            $(this).click();
        }
    });
    
    // Agregar efecto sutil al hacer click
    $('.products_categories a[href^="/shop/category/"]').on('click', function() {
        $(this).css('opacity', '0.7');
        setTimeout(() => {
            $(this).css('opacity', '1');
        }, 150);
    });
});