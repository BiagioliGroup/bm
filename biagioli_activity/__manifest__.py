# -*- coding: utf-8 -*-
{
    'name': 'Biagioli - Actividades con Proyectos',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Crear tareas automáticamente desde actividades',
    'description': """
        Integración de Actividades con Proyectos
        ========================================
        
        Simplifica la gestión creando tareas automáticamente cuando 
        programás una actividad con un proyecto asociado.
        
        Características:
        ---------------
        * Al programar una actividad, podés seleccionar un proyecto
        * Si seleccionás proyecto, se crea automáticamente una tarea
        * La tarea queda vinculada con el registro origen
        * Sincronización entre actividad y tarea
    """,
    'author': 'Biagioli Group',
    'website': 'https://biagioli.com',
    'depends': ['base', 'mail', 'project'],
    'data': [
        # Orden crítico
        'security/security.xml',
        'views/mail_activity_views.xml',
        'views/project_task_views.xml',
        'security/ir.model.access.csv',
        'wizard/schedule_activity_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'biagioli_activity/static/src/js/activity_override.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}