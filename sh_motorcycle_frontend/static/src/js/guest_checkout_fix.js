/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Fix específico para el problema de checkout guest en Biagioli
 * Soluciona errores de querySelector y validación para usuarios no autenticados
 */
publicWidget.registry.BiagioliGuestCheckoutFix = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'submit form[action*="/shop/address/submit"]': '_onAddressFormSubmit',
        'blur input[required], select[required]': '_onRequiredFieldBlur',
        'change select[name="country_id"]': '_onCountryChange',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this._initGuestCheckoutFixes();
        return Promise.resolve();
    },

    /**
     * Inicializa todos los fixes necesarios para usuarios guest
     */
    _initGuestCheckoutFixes: function () {
        console.log('[BIAGIOLI GUEST FIX] Initializing guest checkout fixes');
        
        // Fix 1: Proteger querySelector de elementos undefined
        this._protectQuerySelector();
        
        // Fix 2: Mejorar validación de formularios
        this._enhanceFormValidation();
        
        // Fix 3: Preservar datos de motorcycle
        this._preserveMotorcycleData();
        
        // Fix 4: Manejar errores en URL
        this._handleUrlErrors();
        
        console.log('[BIAGIOLI GUEST FIX] All fixes initialized successfully');
    },

    /**
     * Protege las llamadas a querySelector para evitar errores
     */
    _protectQuerySelector: function () {
        const originalQuerySelector = document.querySelector;
        const originalQuerySelectorAll = document.querySelectorAll;
        
        // Solo aplicar en páginas de checkout
        if (window.location.pathname.includes('/shop/')) {
            document.querySelector = function(selector) {
                try {
                    return originalQuerySelector.call(document, selector);
                } catch (error) {
                    console.warn('[BIAGIOLI GUEST FIX] querySelector error:', selector, error);
                    return null;
                }
            };
            
            document.querySelectorAll = function(selector) {
                try {
                    return originalQuerySelectorAll.call(document, selector);
                } catch (error) {
                    console.warn('[BIAGIOLI GUEST FIX] querySelectorAll error:', selector, error);
                    return [];
                }
            };
        }
    },

    /**
     * Mejora la validación de formularios para usuarios guest
     */
    _enhanceFormValidation: function () {
        const addressForm = document.querySelector('form[action*="/shop/address/submit"]');
        if (!addressForm) return;

        // Agregar validación visual en tiempo real
        const requiredFields = addressForm.querySelectorAll('input[required], select[required]');
        
        requiredFields.forEach(field => {
            if (!field) return;
            
            // Remover validación automática del navegador
            field.removeAttribute('required');
            
            // Agregar validación personalizada
            field.addEventListener('blur', () => {
                this._validateField(field);
            });
            
            field.addEventListener('input', () => {
                if (field.classList.contains('is-invalid')) {
                    this._validateField(field);
                }
            });
        });
        
        console.log('[BIAGIOLI GUEST FIX] Enhanced validation applied to', requiredFields.length, 'fields');
    },

    /**
     * Preserva datos de motorcycle durante el checkout
     */
    _preserveMotorcycleData: function () {
        try {
            // Buscar elementos de motorcycle en el DOM
            const motorcycleSelectors = [
                'select[name="motorcycle_type"], input[name="motorcycle_type"]',
                'select[name="motorcycle_make"], input[name="motorcycle_make"]',
                'select[name="motorcycle_model"], input[name="motorcycle_model"]',
                'select[name="motorcycle_year"], input[name="motorcycle_year"]'
            ];
            
            const motorcycleData = {};
            
            motorcycleSelectors.forEach(selector => {
                const element = document.querySelector(selector);
                if (element && element.value) {
                    const fieldName = element.name;
                    motorcycleData[fieldName] = element.value;
                }
            });
            
            // Guardar en sessionStorage
            if (Object.keys(motorcycleData).length > 0) {
                sessionStorage.setItem('biagioli_motorcycle_data', JSON.stringify(motorcycleData));
                console.log('[BIAGIOLI GUEST FIX] Motorcycle data preserved:', motorcycleData);
            }
            
            // Restaurar datos si es necesario
            const savedData = sessionStorage.getItem('biagioli_motorcycle_data');
            if (savedData) {
                const parsedData = JSON.parse(savedData);
                Object.keys(parsedData).forEach(fieldName => {
                    const element = document.querySelector(`[name="${fieldName}"]`);
                    if (element && !element.value) {
                        element.value = parsedData[fieldName];
                    }
                });
            }
            
        } catch (error) {
            console.warn('[BIAGIOLI GUEST FIX] Motorcycle data handling error:', error);
        }
    },

    /**
     * Maneja errores mostrados en la URL
     */
    _handleUrlErrors: function () {
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        
        if (error) {
            let message = '';
            switch (error) {
                case 'submit_failed':
                    message = 'Hubo un problema al procesar tu información. Por favor, intenta nuevamente.';
                    break;
                case 'missing_fields':
                    message = 'Por favor, completa todos los campos requeridos.';
                    break;
                case 'checkout_failed':
                    message = 'Error en el proceso de checkout. Por favor, revisa tu carrito.';
                    break;
                default:
                    message = 'Ocurrió un error. Por favor, intenta nuevamente.';
            }
            
            this._showErrorMessage(message);
        }
    },

    /**
     * Valida un campo individual
     */
    _validateField: function (field) {
        if (!field) return;

        const value = field.value.trim();
        const isValid = value !== '' && field.checkValidity();
        
        // Remover clases previas
        field.classList.remove('is-valid', 'is-invalid');
        
        // Agregar clase apropiada
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
        }
        
        return isValid;
    },

    /**
     * Maneja el submit del formulario de address
     */
    _onAddressFormSubmit: function (ev) {
        console.log('[BIAGIOLI GUEST FIX] Form submit intercepted');
        
        const form = ev.currentTarget;
        if (!form) return;

        // Preservar datos de motorcycle antes del submit
        this._preserveMotorcycleData();
        
        // Validar campos requeridos
        const requiredFields = [
            form.querySelector('input[name="name"]'),
            form.querySelector('input[name="email"]'),
            form.querySelector('input[name="street"]'),
            form.querySelector('input[name="city"]'),
            form.querySelector('select[name="country_id"]')
        ].filter(field => field !== null);
        
        let isValid = true;
        let firstInvalidField = null;
        
        requiredFields.forEach(field => {
            if (!this._validateField(field)) {
                isValid = false;
                if (!firstInvalidField) {
                    firstInvalidField = field;
                }
            }
        });
        
        if (!isValid) {
            ev.preventDefault();
            if (firstInvalidField) {
                firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalidField.focus();
            }
            this._showErrorMessage('Por favor, completa todos los campos requeridos correctamente.');
            return false;
        }
        
        console.log('[BIAGIOLI GUEST FIX] Form validation passed, submitting');
    },

    /**
     * Maneja blur en campos requeridos
     */
    _onRequiredFieldBlur: function (ev) {
        this._validateField(ev.currentTarget);
    },

    /**
     * Maneja cambios en el país
     */
    _onCountryChange: function (ev) {
        const countrySelect = ev.currentTarget;
        if (!countrySelect || !countrySelect.value) return;

        // Actualizar campos de estado
        this._updateStateField(countrySelect.value);
    },

    /**
     * Actualiza el campo de estado basado en el país
     */
    _updateStateField: function (countryId) {
        const stateSelect = document.querySelector('select[name="state_id"]');
        if (!stateSelect) return;

        // Llamada AJAX para obtener estados
        this._rpc({
            route: `/shop/country_infos/${countryId}`,
            params: {}
        }).then(data => {
            // Limpiar opciones existentes
            stateSelect.innerHTML = '<option value="">Estado / Provincia</option>';
            
            // Agregar nuevas opciones
            if (data.states && data.states.length > 0) {
                data.states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state[0];
                    option.textContent = state[1];
                    stateSelect.appendChild(option);
                });
                stateSelect.parentNode.style.display = 'block';
            } else {
                stateSelect.parentNode.style.display = 'none';
            }
        }).catch(error => {
            console.warn('[BIAGIOLI GUEST FIX] Error updating states:', error);
        });
    },

    /**
     * Muestra un mensaje de error al usuario
     */
    _showErrorMessage: function (message) {
        // Remover mensaje existente
        const existingMessage = document.querySelector('.biagioli-error-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        // Crear nuevo mensaje
        const messageDiv = document.createElement('div');
        messageDiv.className = 'alert alert-warning alert-dismissible fade show biagioli-error-message';
        messageDiv.innerHTML = `
            <strong>Atención:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        `;

        // Insertar al inicio del contenido
        const container = document.querySelector('#wrap .container') || document.querySelector('#wrap');
        if (container) {
            container.insertBefore(messageDiv, container.firstChild);
        }

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (messageDiv && messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
});

// Export para uso en otros módulos si es necesario
export default publicWidget.registry.BiagioliGuestCheckoutFix;