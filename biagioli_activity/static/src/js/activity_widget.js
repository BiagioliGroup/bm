/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ActivityMenuView } from "@mail/core/web/activity_menu_view";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

/**
 * Extiende el widget de actividades para incluir funcionalidad de proyecto
 */
patch(ActivityMenuView.prototype, {
  setup() {
    super.setup();
    this.actionService = useService("action");
    this.notificationService = useService("notification");
  },

  /**
   * Override para agregar proyecto al programar actividad
   */
  async scheduleActivity() {
    const action = await super.scheduleActivity();

    // Agregar contexto para el wizard personalizado
    if (action && action.context) {
      action.context.default_create_task = false;
      action.context.default_create_todo = true;

      // Si el usuario es de proyecto, sugerir crear tarea
      const userService = useService("user");
      const user = await userService.load();
      if (user.hasGroup("project.group_project_user")) {
        action.context.default_create_task = true;
        action.context.default_create_todo = false;
      }
    }

    return action;
  },

  /**
   * Extender para mostrar información de proyecto en actividades
   */
  async onActivityClick(activity) {
    // Si la actividad tiene proyecto, mostrarlo
    if (activity.project_id) {
      this.notificationService.add(
        `Actividad vinculada al proyecto: ${activity.project_id[1]}`,
        { type: "info" }
      );
    }

    return super.onActivityClick(activity);
  },

  /**
   * Agregar acción para ver tareas/todos creados
   */
  async viewLinkedItems(activity) {
    let action = false;

    if (activity.linked_task_id) {
      action = {
        type: "ir.actions.act_window",
        name: "Tarea Vinculada",
        res_model: "project.task",
        res_id: activity.linked_task_id[0],
        view_mode: "form",
        target: "current",
      };
    } else if (activity.linked_todo_id) {
      action = {
        type: "ir.actions.act_window",
        name: "To-Do Vinculado",
        res_model: "project.todo",
        res_id: activity.linked_todo_id[0],
        view_mode: "form",
        target: "current",
      };
    }

    if (action) {
      return this.actionService.doAction(action);
    }
  },
});

/**
 * Registro de acciones rápidas para crear to-dos
 */
registry.category("quick_create").add("project_todo_quick_create", {
  Component: class TodoQuickCreate {
    static template = "schedule_activity_project_integration.TodoQuickCreate";

    setup() {
      this.orm = useService("orm");
      this.actionService = useService("action");
    }

    async createTodo(name) {
      const todoId = await this.orm.create("project.todo", [
        {
          name: name,
          state: "open",
          priority: "normal",
          user_ids: [[6, 0, [this.env.user.id]]],
        },
      ]);

      // Abrir el to-do creado
      return this.actionService.doAction({
        type: "ir.actions.act_window",
        res_model: "project.todo",
        res_id: todoId,
        view_mode: "form",
        target: "current",
      });
    }
  },
  sequence: 10,
});

/**
 * Widget para mostrar estado de integración
 */
registry.category("fields").add("activity_project_status", {
  component: class ActivityProjectStatus {
    static template =
      "schedule_activity_project_integration.ActivityProjectStatus";

    get statusInfo() {
      const record = this.props.record;

      if (record.data.linked_task_id) {
        return {
          icon: "fa-tasks",
          text: "Tarea Creada",
          class: "text-success",
        };
      } else if (record.data.linked_todo_id) {
        return {
          icon: "fa-check-square-o",
          text: "To-Do Creado",
          class: "text-info",
        };
      } else if (record.data.project_id) {
        return {
          icon: "fa-folder",
          text: "Creará tarea",
          class: "text-warning",
        };
      } else {
        return {
          icon: "fa-calendar",
          text: "Creará to-do",
          class: "text-muted",
        };
      }
    }
  },
});
