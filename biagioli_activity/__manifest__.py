# -*- coding: utf-8 -*-
{
    'name': 'Biagioli - Actividades con Proyectos',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Crear tareas automáticamente desde actividades',
    'description': """
        Integración de Actividades con Proyectos - Biagioli Group
        ==========================================================
        
        Este módulo extiende el wizard estándar de actividades para agregar
        la opción de vincular con proyectos y crear tareas automáticamente.
        
        Características:
        ---------------
        * Campo "Proyecto" en el wizard estándar de actividades
        * Creación automática de tareas cuando se selecciona proyecto
        * Vinculación completa entre actividad, tarea y registro origen
        * Funciona en TODOS los módulos (Ventas, Compras, CRM, etc.)
        
        Uso:
        ----
        1. En cualquier formulario, click en "Actividades" → "Programar"
        2. Aparece el wizard estándar CON el campo Proyecto
        3. Si seleccionás proyecto → Se crea tarea automáticamente
        4. Si NO seleccionás proyecto → Comportamiento estándar
    """,
    'author': 'Biagioli Group',
    'website': 'https://biagioli.com',
    'depends': ['base', 'mail', 'project'],
    'data': [
        # 1° Seguridad
        'security/ir.model.access.csv',
        
        # 2° Vistas de modelos
        'views/project_task_views.xml',
        'views/mail_activity_views.xml', 
        'views/mail_activity_schedule_views.xml',
        
        # 3° Wizard 
        'wizard/schedule_activity_wizard_views.xml',
        
        # 4° Datos y cron jobs
        'data/cron_jobs_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}