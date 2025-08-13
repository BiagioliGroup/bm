/** @odoo-module **/
// Archivo: sh_motorcycle_backend/static/src/js/guest_checkout_fix.js

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Widget defensivo para arreglar problemas de checkout con usuarios guest
 * Específicamente para el error de querySelector en /shop/address
 */
publicWidget.registry.BiagioliGuestCheckoutFix = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'submit form[action*="/shop/address/submit"]': '_onAddressFormSubmit',
        'click #save_address': '_onSaveAddressClick',
        'blur input[required], select[required]': '_onRequiredFieldBlur',
    },

    /**
     * @override
     */
    start: function () {
        console.log('[BIAGIOLI] Guest checkout fix widget started');
        this._super.apply(this, arguments);
        this._initGuestCheckoutFixes();
        return Promise.resolve();
    },

    /**
     * Inicializa las correcciones defensivas para checkout guest
     */
    _initGuestCheckoutFixes: function () {
        // Solo aplicar fixes en páginas de checkout
        if (!window.location.pathname.includes('/shop/')) {
            return;
        }

        // Verificar si estamos en modo guest
        const isGuest = document.querySelector('[data-user-guest="True"]') !== null;
        
        console.log('[BIAGIOLI] Initializing guest checkout fixes');
        console.log('[BIAGIOLI] User is guest:', isGuest);
        console.log('[BIAGIOLI] Current URL:', window.location.href);
        console.log('[BIAGIOLI] User agent:', navigator.userAgent);
        
        // Fix 1: Proteger querySelector calls
        this._protectQuerySelectors();
        
        // Fix 2: Validación de formulario defensiva
        this._enhanceFormValidation();
        
        // Fix 3: Manejo de errores de motorcycle frontend
        this._protectMotorcycleFrontend();
        
        // Fix 4: Mostrar mensajes de error URL params
        this._handleUrlErrors();
        
        // Fix 5: Debug específico para guest users
        if (isGuest) {
            this._initGuestDebugging();
        }
    },

    /**
     * Protege las llamadas a querySelector que pueden fallar
     */
    _protectQuerySelectors: function () {
        // Wrapper defensivo para querySelector
        const originalQS = document.querySelector;
        const originalQSA = document.querySelectorAll;
        
        document.querySelector = function(selector) {
            try {
                return originalQS.call(this, selector);
            } catch (e) {
                console.warn('[BIAGIOLI] querySelector protected:', selector, e);
                return null;
            }
        };
        
        document.querySelectorAll = function(selector) {
            try {
                return originalQSA.call(this, selector);
            } catch (e) {
                console.warn('[BIAGIOLI] querySelectorAll protected:', selector, e);
                return [];
            }
        };
    },

    /**
     * Mejora la validación del formulario de address
     */
    _enhanceFormValidation: function () {
        const addressForm = document.querySelector('form[action*="/shop/address/submit"]');
        if (!addressForm) return;

        console.log('[BIAGIOLI] Enhanced form validation applied');
        
        // Agregar indicadores visuales de validación
        const requiredFields = addressForm.querySelectorAll('input[required], select[required]');
        
        requiredFields.forEach(field => {
            if (!field) return;
            
            // Validación en tiempo real
            field.addEventListener('input', () => {
                this._validateField(field);
            });
            
            field.addEventListener('change', () => {
                this._validateField(field);
            });
        });
    },

    /**
     * Protege el código del módulo motorcycle frontend
     */
    _protectMotorcycleFrontend: function () {
        // Envolver funciones potencialmente problemáticas
        if (window.sh_motorcycle) {
            const originalFunctions = {};
            
            // Proteger funciones comunes que podrían fallar
            ['get_type_list', 'get_make_list', 'get_model_list', 'get_year_list'].forEach(funcName => {
                if (typeof window.sh_motorcycle[funcName] === 'function') {
                    originalFunctions[funcName] = window.sh_motorcycle[funcName];
                    
                    window.sh_motorcycle[funcName] = function(...args) {
                        try {
                            return originalFunctions[funcName].apply(this, args);
                        } catch (e) {
                            console.warn(`[BIAGIOLI] Protected sh_motorcycle.${funcName}:`, e);
                            return []; // Return empty array as fallback
                        }
                    };
                }
            });
        }
    },

    /**
     * Debugging específico para usuarios guest
     */
    _initGuestDebugging: function () {
        console.log('[BIAGIOLI] =================================');
        console.log('[BIAGIOLI] GUEST DEBUGGING ACTIVATED');
        console.log('[BIAGIOLI] =================================');
        
        // Log info del DOM
        const form = document.querySelector('form[data-biagioli-debug]');
        const submitBtn = document.querySelector('[data-biagioli-submit]');
        const requiredFields = document.querySelectorAll('input[required], select[required]');
        
        console.log('[BIAGIOLI] Form found:', !!form);
        console.log('[BIAGIOLI] Submit button found:', !!submitBtn);
        console.log('[BIAGIOLI] Required fields count:', requiredFields.length);
        
        // Log info de motorcycle
        console.log('[BIAGIOLI] sh_motorcycle available:', typeof window.sh_motorcycle !== 'undefined');
        
        // Log errores de JS si existen
        window.addEventListener('error', (e) => {
            console.error('[BIAGIOLI] JavaScript Error Detected:', {
                message: e.message,
                filename: e.filename,
                lineno: e.lineno,
                colno: e.colno,
                error: e.error
            });
        });
        
        // Log problemas de querySelector
        const originalQS = document.querySelector;
        document.querySelector = function(selector) {
            try {
                const result = originalQS.call(this, selector);
                if (!result && selector.includes('motorcycle')) {
                    console.warn('[BIAGIOLI] Motorcycle selector not found:', selector);
                }
                return result;
            } catch (e) {
                console.error('[BIAGIOLI] querySelector error for:', selector, e);
                return null;
            }
        };
        
        // Mostrar banner de debugging
        this._showGuestDebugBanner();
    },

    /**
     * Muestra banner de debugging para guest users
     */
    _showGuestDebugBanner: function () {
        const banner = document.createElement('div');
        banner.className = 'biagioli-debug-banner';
        banner.innerHTML = '🔧 BIAGIOLI DEBUG MODE - Guest Checkout Testing Active';
        document.body.appendChild(banner);
        
        // Auto-remover después de 10 segundos con fade out
        setTimeout(() => {
            if (banner && banner.parentNode) {
                banner.classList.add('fade-out');
                setTimeout(() => {
                    banner.remove();
                }, 500);
            }
        }, 10000);
    },
    _handleUrlErrors: function () {
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        
        if (error) {
            let message = '';
            
            switch (error) {
                case 'address_error':
                    message = 'Hubo un problema cargando el formulario de dirección. Por favor, intenta nuevamente.';
                    break;
                case 'submit_validation':
                    message = 'Error de validación en el formulario. Verifica que todos los campos estén completos.';
                    break;
                case 'submit_required_fields':
                    message = 'Faltan campos obligatorios. Por favor, completa toda la información requerida.';
                    break;
                case 'checkout_failed':
                    message = 'Error en el proceso de checkout. Por favor, revisa tu carrito e intenta nuevamente.';
                    break;
                default:
                    if (error.startsWith('missing_fields=')) {
                        const fields = error.replace('missing_fields=', '').split(',');
                        message = `Faltan los siguientes campos: ${fields.join(', ')}`;
                    } else {
                        message = 'Ha ocurrido un error. Por favor, intenta nuevamente.';
                    }
            }
            
            if (message) {
                this._showErrorMessage(message);
            }
        }
    },

    /**
     * Valida un campo individual
     */
    _validateField: function (field) {
        if (!field) return;

        const isValid = field.checkValidity() && field.value.trim() !== '';
        
        // Remover clases anteriores
        field.classList.remove('is-valid', 'is-invalid');
        
        // Agregar clase apropiada
        if (field.value.trim() !== '') {
            field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        }
        
        // Manejar mensaje de error
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
     * Maneja el submit del formulario de address
     */
    _onAddressFormSubmit: function (ev) {
        console.log('[BIAGIOLI] Address form submit intercepted');
        
        const form = ev.currentTarget;
        if (!form) return;

        // Validación defensiva antes del submit
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
            
            this._showErrorMessage('Por favor, completa todos los campos obligatorios antes de continuar.');
            return false;
        }

        console.log('[BIAGIOLI] Form validation passed, allowing submit');
    },

    /**
     * Maneja el click en el botón de guardar dirección
     */
    _onSaveAddressClick: function (ev) {
        console.log('[BIAGIOLI] Save address clicked');
        // El manejo se hace en _onAddressFormSubmit
    },

    /**
     * Maneja blur en campos requeridos
     */
    _onRequiredFieldBlur: function (ev) {
        this._validateField(ev.currentTarget);
    },

    /**
     * Muestra un mensaje de error al usuario
     */
    _showErrorMessage: function (message) {
        // Remover mensajes existentes
        const existingAlerts = document.querySelectorAll('.biagioli-error-alert');
        existingAlerts.forEach(alert => alert.remove());

        // Crear nuevo mensaje
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning alert-dismissible fade show biagioli-error-alert mt-3';
        alertDiv.innerHTML = `
            <strong>Atención:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insertar en el contenedor principal
        const container = document.querySelector('.container-fluid') || 
                         document.querySelector('.container') || 
                         document.querySelector('#wrap');
        
        if (container) {
            container.insertBefore(alertDiv, container.firstElementChild);
            
            // Scroll al mensaje
            alertDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // Auto-remover después de 8 segundos
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 8000);
    },
});

// Funciones de debugging globales para testing en consola
window.BiagioliDebug = {
    checkElements: function() {
        console.log('=== BIAGIOLI ELEMENT CHECK ===');
        console.log('Form:', document.querySelector('form[data-biagioli-debug]'));
        console.log('Submit button:', document.querySelector('[data-biagioli-submit]'));
        console.log('Required fields:', document.querySelectorAll('input[required], select[required]').length);
        console.log('Motorcycle available:', typeof window.sh_motorcycle !== 'undefined');
    },
    
    triggerSubmit: function() {
        const form = document.querySelector('form[data-biagioli-debug]');
        if (form) {
            console.log('[BIAGIOLI] Triggering form submit');
            form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        } else {
            console.error('[BIAGIOLI] Form not found');
        }
    },
    
    showFormData: function() {
        const form = document.querySelector('form[data-biagioli-debug]');
        if (form) {
            const formData = new FormData(form);
            console.log('=== FORM DATA ===');
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
        }
    }
};

// Export del widget para debugging
window.BiagioliGuestCheckoutFix = publicWidget.registry.BiagioliGuestCheckoutFix;

console.log('[BIAGIOLI] Guest checkout fix script loaded');
console.log('[BIAGIOLI] Debug functions available: window.BiagioliDebug');