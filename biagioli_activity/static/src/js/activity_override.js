/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ActivityController } from "@mail/components/activity/activity_controller";

/**
 * Override del controlador de actividades para usar nuestro wizard personalizado
 */
patch(ActivityController.prototype, {
  /**
   * Override para abrir nuestro wizard en lugar del estándar
   */
  async scheduleActivity() {
    // Abrir nuestro wizard personalizado
    return this.actionService.doAction({
      type: "ir.actions.act_window",
      res_model: "schedule.activity.wizard",
      views: [[false, "form"]],
      view_mode: "form",
      target: "new",
      context: {
        ...this.props.context,
        default_res_model: this.props.resModel,
        default_res_id: this.props.resId,
        active_model: this.props.resModel,
        active_id: this.props.resId,
        active_ids: [this.props.resId],
      },
    });
  },
});
