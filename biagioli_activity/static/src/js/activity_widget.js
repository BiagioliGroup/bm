/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Override para el botón de programar actividad en el chatter
 */
const scheduleActivityAction = {
  type: "ir.actions.act_window",
  res_model: "schedule.activity.wizard",
  views: [[false, "form"]],
  view_mode: "form",
  target: "new",
  name: "Programar Actividad con Proyecto",
};

// Registrar un servicio para interceptar la acción de programar actividad
registry.category("services").add("biagioli_activity_service", {
  start(env) {
    // Interceptar cuando se abre el popup de actividad
    const originalDoAction = env.services.action.doAction;

    env.services.action.doAction = async function (action, options) {
      // Verificar si es el wizard de actividad estándar
      if (action && typeof action === "object") {
        if (
          action.res_model === "mail.activity" &&
          action.type === "ir.actions.act_window"
        ) {
          // Si es una nueva actividad (no edición)
          if (!action.res_id && action.target === "new") {
            // Reemplazar con nuestro wizard
            const context = action.context || {};

            return originalDoAction.call(
              this,
              {
                ...scheduleActivityAction,
                context: {
                  ...context,
                  default_res_model: context.default_res_model,
                  default_res_id: context.default_res_id,
                  active_model: context.default_res_model,
                  active_id: context.default_res_id,
                },
              },
              options
            );
          }
        }
      }

      // Para cualquier otra acción, usar el comportamiento original
      return originalDoAction.call(this, action, options);
    };

    return {
      // No necesitamos exponer nada
    };
  },
});
