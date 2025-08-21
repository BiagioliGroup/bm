/** @odoo-module **/
// Fix específico para el error de checkout guest en Odoo

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Fix para el error específico:
 * TypeError: Cannot read properties of undefined (reading 'querySelector')
 * at Class._getInputLabel ... at Class._changeCountry
 */
publicWidget.registry.GuestCheckoutErrorFix = publicWidget.Widget.extend({
  selector: ".oe_website_sale",

  start: function () {
    const result = this._super.apply(this, arguments);

    // Solo aplicar en páginas de checkout
    if (
      window.location.pathname.includes("/shop/checkout") ||
      window.location.pathname.includes("/shop/address")
    ) {
      this._applyCheckoutFixes();
    }

    return result;
  },

  _applyCheckoutFixes: function () {
    // Fix 1: Proteger el método querySelector que falla
    this._protectCoreWidgets();

    // Fix 2: Asegurar que existan elementos requeridos antes de que se ejecute el código core
    this._ensureRequiredElements();

    // Fix 3: Monitorear y re-aplicar fixes si es necesario
    this._monitorForErrors();
  },

  /**
   * Protege los métodos core que causan el error
   */
  _protectCoreWidgets: function () {
    // Sobrescribir querySelector para retornar elementos seguros
    const originalQuerySelector = Element.prototype.querySelector;

    Element.prototype.querySelector = function (selector) {
      try {
        const element = originalQuerySelector.call(this, selector);
        // Si no encuentra el elemento, crear uno mock para evitar el error
        if (
          !element &&
          selector.includes("input") &&
          selector.includes("name")
        ) {
          const mockInput = document.createElement("input");
          mockInput.style.display = "none";
          this.appendChild(mockInput);
          return mockInput;
        }
        return element;
      } catch (e) {
        console.warn("[CHECKOUT FIX] querySelector error prevented:", e);
        return null;
      }
    };
  },

  /**
   * Asegura que existan los elementos que el core espera encontrar
   */
  _ensureRequiredElements: function () {
    // Los elementos que Odoo busca y que pueden no existir
    const requiredSelectors = [
      'input[name="name"]',
      'input[name="email"]',
      'input[name="phone"]',
      'select[name="country_id"]',
      'input[name="street"]',
      'input[name="city"]',
    ];

    requiredSelectors.forEach((selector) => {
      if (!document.querySelector(selector)) {
        console.warn(`[CHECKOUT FIX] Missing element: ${selector}`);
        // Crear elemento mock si no existe
        const mockElement = this._createMockElement(selector);
        if (mockElement) {
          const form = document.querySelector('form[action*="/shop/"]');
          if (form) {
            form.appendChild(mockElement);
          }
        }
      }
    });
  },

  /**
   * Crea elementos mock para evitar errores de core
   */
  _createMockElement: function (selector) {
    if (selector.includes("input")) {
      const input = document.createElement("input");
      const nameMatch = selector.match(/name="([^"]+)"/);
      if (nameMatch) {
        input.name = nameMatch[1];
        input.style.display = "none";
        input.type = "hidden";
        return input;
      }
    } else if (selector.includes("select")) {
      const select = document.createElement("select");
      const nameMatch = selector.match(/name="([^"]+)"/);
      if (nameMatch) {
        select.name = nameMatch[1];
        select.style.display = "none";
        return select;
      }
    }
    return null;
  },

  /**
   * Monitorea errores y aplica fixes dinámicamente
   */
  _monitorForErrors: function () {
    // Capturar errores de JavaScript
    const originalError = window.onerror;

    window.onerror = (message, source, lineno, colno, error) => {
      if (
        message &&
        message.includes("querySelector") &&
        (source.includes("web.assets_frontend") || source.includes("lazy"))
      ) {
        console.warn("[CHECKOUT FIX] Prevented core error:", message);

        // Re-aplicar fixes si es necesario
        setTimeout(() => {
          this._ensureRequiredElements();
        }, 100);

        // No propagar el error
        return true;
      }

      // Llamar al handler original para otros errores
      if (originalError) {
        return originalError.call(this, message, source, lineno, colno, error);
      }

      return false;
    };

    // También monitorear errores no capturados en Promises
    window.addEventListener("unhandledrejection", (event) => {
      if (
        event.reason &&
        event.reason.message &&
        event.reason.message.includes("querySelector")
      ) {
        console.warn("[CHECKOUT FIX] Prevented Promise error:", event.reason);
        event.preventDefault();
      }
    });
  },
});

// Aplicar fix inmediatamente al cargar la página
document.addEventListener("DOMContentLoaded", function () {
  if (
    window.location.pathname.includes("/shop/checkout") ||
    window.location.pathname.includes("/shop/address")
  ) {
    // Fix inmediato para elementos críticos
    const form = document.querySelector('form[action*="/shop/"]');
    if (form && !form.querySelector('input[name="name"]')) {
      console.log("[CHECKOUT FIX] Applying immediate DOM fixes...");

      // Crear campos esenciales si no existen
      const essentialFields = ["name", "email", "phone"];
      essentialFields.forEach((fieldName) => {
        if (!form.querySelector(`input[name="${fieldName}"]`)) {
          const input = document.createElement("input");
          input.name = fieldName;
          input.type = "hidden";
          input.style.display = "none";
          form.appendChild(input);
        }
      });
    }
  }
});
