# -*- coding: utf-8 -*-
{
    'name': 'Biagioli - Integración Actividades',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Generar Tareas de Proyecto o To-Dos desde Actividades Programadas',
    'description': """
        Integración de Actividades con Proyectos - Biagioli
        ===================================================
        
        Este módulo mejora la gestión de proyectos en Odoo automatizando la creación 
        de tareas y to-dos directamente desde las actividades programadas.
        
        Características Principales:
        ---------------------------
        * Convertir actividades programadas en tareas de proyecto
        * Crear to-dos desde actividades para usuarios internos
        * Vinculación automática de recursos (nombre, modelo, ID)
        * Manejo inteligente de permisos de usuario
        * Soporte para todos los tipos de actividades
        
        Flujo de Trabajo:
        ----------------
        1. Usuarios Internos: Actividades → To-Dos
        2. Usuarios de Proyecto con proyecto: Actividades → Tareas
        3. Usuarios de Proyecto sin proyecto: Actividades → Tareas + To-Dos
    """,
    'author': 'Biagioli Group',
    'website': 'https://biagioli.com',
    'depends': [
        'base',
        'mail',
        'project',
    ],
    'data': [
        # Primero seguridad - solo grupos
        'security/security.xml',
        
        # Luego vistas que registran los modelos
        'views/project_todo_views.xml',
        'views/mail_activity_views.xml',
        'views/project_task_views.xml',
        
        # Después permisos CSV (ahora que los modelos existen)
        'security/ir.model.access.csv',
        
        # Finalmente wizards
        'wizard/schedule_activity_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'biagioli_activity/static/src/js/activity_widget.js',
            'biagioli_activity/static/src/scss/activity_style.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}