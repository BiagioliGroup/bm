# -*- coding: utf-8 -*-
{
    'name': 'Schedule Activity Project Integrati    on',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Generar Tareas de Proyecto o To-Dos desde Actividades Programadas',
    'description': """
        Integración de Actividades con Proyectos
        ========================================
        
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
    'author': 'Tu Empresa',
    'website': 'https://tuempresa.com',
    'depends': [
        'base',
        'mail',
        'project',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        'security/security.xml',
        
        # Vistas
        'views/mail_activity_views.xml',
        'views/project_task_views.xml',
        'views/project_todo_views.xml',
        
        # Wizards
        'wizard/schedule_activity_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'schedule_activity_project_integration/static/src/js/activity_widget.js',
            'schedule_activity_project_integration/static/src/scss/activity_style.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}