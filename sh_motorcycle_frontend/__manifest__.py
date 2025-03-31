# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Auto Parts Website",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": """
Auto Parts Website,Find Perfect Vehicle Auto Parts Module,
Choose Auto Parts Base On Vehicle Make , Find Auto Parts Based On Model,
Type App , Search Auto Parts Based On Model Year Odoo
""",
    "description": """
This module makes searching for auto parts it's as easy peasy.
In website search tool helps in choosing your auto parts base on vehicle make,
vehicle model, type and model year very easily.
Enter the vehicle details in the search field,
click the SEARCH button so it will display available auto parts.
You can easily set button size, Ecommerce Category.
Users can save searched auto parts.
Logged users can also see the saved item list in 'My Garage' Dropdown list.
User can save search items and remove from 'My Garage'.
Users can sort search results.
This website is very perspicuous to the user and easy to interact with the site.
Auto Parts Website Odoo
Easily Search Auto Parts Module, Choose Auto Parts Base On Vehicle Make,
Model ,Type And Model Year Odoo.
Find Perfect Vehicle Auto Parts Module, Choose Auto Parts Base On Vehicle Make,
Find Auto Parts Based On Model ,Type App , Search Auto Parts Based On Model Year Odoo
""",
    "version": "0.0.1",
    "depends": [
        "sh_motorcycle_backend",
        "website_sale",
        "portal",
    ],
    "data": [
        "views/website_sale_templates.xml",
        "views/res_config_settings_view.xml",
        "views/sh_morotcycle_garage_templates.xml",
        "views/sh_motorcycle_frontend_snippet_templates.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'sh_motorcycle_frontend/static/src/js/search.js',
            'sh_motorcycle_frontend/static/src/scss/custom.scss',
            'sh_motorcycle_frontend/static/src/js/snippets.js',
            'sh_motorcycle_frontend/static/src/scss/snippets.scss',
            'sh_motorcycle_frontend/static/src/js/variant_code_update.js',
        ],
        'website.assets_wysiwyg': [
            'sh_motorcycle_frontend/static/src/js/editor.js',
        ],
    },
    "images": ["static/description/background.png", ],
    "application": True,
    "auto_install": False,
    "installable": True,
    "price": 100,
    "currency": "EUR"
}
