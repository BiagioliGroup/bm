/** @odoo-module **/
// Archivo: sh_motorcycle_backend/static/src/js/guest_checkout_fix.js
// VERSIÓN PRODUCCIÓN - Sin debug visual, solo fixes esenciales

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Fix defensivo para checkout de usuarios guest
 * Versión optimizada para producción sin elementos de debug
 */
publicWidget.registry.BiagioliGuestCheckoutFix = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'submit form[action*="/shop/address/submit"]': '_onAddressFormSubmit',
        'blur input[required], select[required]': '_onRequiredFieldBlur',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        
        // Solo aplicar en páginas de checkout
        if (window.location.pathname.includes('/shop/')) {
            this._initProductionFixes();
        }
        
        return Promise.resolve();
    },
    

    /**
     * Inicializa fixes para producción (sin debug)
     */
    _initProductionFixes: function () {
        // Fix 1: Protección de querySelector
        this._protectQuerySelectors();
        
        // Fix 2: Validación de formularios
        this._enhanceFormValidation();
        
        // Fix 3: Protección de motorcycle frontend
        this._protectMotorcycleFrontend();
        
        // Fix 4: Manejo de errores de URL
        this._handleUrlErrors();
    },

    /**
     * Protección defensiva para querySelector
     */
    _protectQuerySelectors: function () {
        const originalQS = document.querySelector;
        const originalQSA = document.querySelectorAll;
        
        document.querySelector = function(selector) {
            try {
                return originalQS.call(this, selector);
            } catch (e) {
                // Silencioso en producción
                return null;
            }
        };
        
        document.querySelectorAll = function(selector) {
            try {
                return originalQSA.call(this, selector);
            } catch (e) {
                // Silencioso en producción
                return [];
            }
        };
    },

    /**
     * Validación mejorada de formularios
     */
    _enhanceFormValidation: function () {
        const addressForm = document.querySelector('form[action*="/shop/address/submit"]');
        if (!addressForm) return;

        const requiredFields = addressForm.querySelectorAll('input[required], select[required]');
        
        requiredFields.forEach(field => {
            if (!field) return;
            
            field.addEventListener('input', () => {
                this._validateField(field);
            });
            
            field.addEventListener('change', () => {
                this._validateField(field);
            });
        });
    },

    /**
     * Protección para motorcycle frontend
     */
    _protectMotorcycleFrontend: function () {
        if (!window.sh_motorcycle) return;

        const protectedFunctions = ['get_type_list', 'get_make_list', 'get_model_list', 'get_year_list'];
        
        protectedFunctions.forEach(funcName => {
            if (typeof window.sh_motorcycle[funcName] === 'function') {
                const originalFunc = window.sh_motorcycle[funcName];
                
                window.sh_motorcycle[funcName] = function(...args) {
                    try {
                        return originalFunc.apply(this, args);
                    } catch (e) {
                        // Retorno seguro en caso de error
                        return [];
                    }
                };
            }
        });
    },

    /**
     * Manejo de errores en URL parameters
     */
    _handleUrlErrors: function () {
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        
        if (!error) return;

        let message = '';
        
        switch (error) {
            case 'address_error':
                message = 'Hubo un problema cargando el formulario. Por favor, intenta nuevamente.';
                break;
            case 'validation':
                message = 'Por favor, verifica que todos los campos estén completos.';
                break;
            case 'submit_failed':
                message = 'Error al procesar el formulario. Intenta nuevamente.';
                break;
            default:
                if (error.startsWith('missing=')) {
                    const fields = error.replace('missing=', '').split(',');
                    message = `Faltan campos obligatorios: ${fields.join(', ')}`;
                }
        }
        
        if (message) {
            this._showErrorMessage(message);
        }
    },

    /**
     * Validación individual de campos
     */
    _validateField: function (field) {
        if (!field) return;

        const isValid = field.checkValidity() && field.value.trim() !== '';
        
        field.classList.remove('is-valid', 'is-invalid');
        
        if (field.value.trim() !== '') {
            field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        }
        
        // Manejo de mensaje de error
        const errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (!isValid && field.value.trim() !== '') {
            if (!errorElement) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'Este campo es obligatorio';
                field.parentNode.appendChild(errorDiv);
            }
        } else if (errorElement) {
            errorElement.remove();
        }
    },

    /**
     * Validación en submit del formulario
     */
    _onAddressFormSubmit: function (ev) {
        const form = ev.currentTarget;
        if (!form) return;

        const requiredFields = form.querySelectorAll('input[required], select[required]');
        let isValid = true;
        let firstInvalidField = null;

        requiredFields.forEach(field => {
            if (!field) return;
            
            if (!field.value || !field.value.trim()) {
                this._validateField(field);
                isValid = false;
                if (!firstInvalidField) {
                    firstInvalidField = field;
                }
            }
        });

        if (!isValid) {
            ev.preventDefault();
            ev.stopPropagation();
            
            if (firstInvalidField) {
                firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalidField.focus();
            }
            
            this._showErrorMessage('Por favor, completa todos los campos obligatorios.');
            return false;
        }
    },

    /**
     * Validación en blur de campos requeridos
     */
    _onRequiredFieldBlur: function (ev) {
        this._validateField(ev.currentTarget);
    },

    /**
     * Mostrar mensaje de error (versión mínima para producción)
     */
    _showErrorMessage: function (message) {
        // Remover mensajes existentes
        const existingAlerts = document.querySelectorAll('.biagioli-error-alert');
        existingAlerts.forEach(alert => alert.remove());

        // Crear mensaje mínimo
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning alert-dismissible fade show biagioli-error-alert mt-3';
        alertDiv.innerHTML = `
            <strong>Atención:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insertar en contenedor principal
        const container = document.querySelector('.container-fluid') || 
                         document.querySelector('.container') || 
                         document.querySelector('#wrap');
        
        if (container) {
            container.insertBefore(alertDiv, container.firstElementChild);
        }

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    },
});

// No exportar funciones de debug en producción