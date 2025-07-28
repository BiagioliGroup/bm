"""Test helpers for creating module-agnostic test data.

This module provides utilities to create test records that work regardless
of which Odoo modules are installed. It dynamically detects required fields
and provides safe defaults.
"""

import logging

_logger = logging.getLogger(__name__)


class TestHelpers:
    """Utilities for creating test data that works with any installed modules."""

    _cache = {}

    @classmethod
    def get_required_defaults(cls, env, model_name):
        """Get required field defaults for a model.

        Args:
            env: Odoo environment
            model_name: Name of the model (e.g. 'res.partner')

        Returns:
            dict: Dictionary of field_name: default_value for required fields
        """
        cache_key = f"{env.cr.dbname}:{model_name}"
        if cache_key in cls._cache:
            return cls._cache[cache_key].copy()

        model = env[model_name]
        defaults = {}

        # Get field information
        fields_info = model.fields_get()

        # Get default values from the model
        model_defaults = model.default_get(list(fields_info.keys()))

        for field_name, field_info in fields_info.items():
            # Skip computed, related, and readonly fields
            if field_info.get("compute") or field_info.get("related") or field_info.get("readonly"):
                continue

            # Check if field is required
            if field_info.get("required"):
                # First check if there's a default value from default_get
                if field_name in model_defaults:
                    defaults[field_name] = model_defaults[field_name]
                    continue

                # Otherwise provide safe defaults based on field type
                field_type = field_info.get("type")

                if field_type == "selection":
                    # Use first available option
                    selection = field_info.get("selection", [])
                    if selection and isinstance(selection, list) and len(selection) > 0:
                        defaults[field_name] = selection[0][0]
                elif field_type == "boolean":
                    defaults[field_name] = False
                elif field_type in ("integer", "float", "monetary"):
                    defaults[field_name] = 0
                elif field_type in ("char", "text", "html"):
                    defaults[field_name] = ""
                elif field_type == "date":
                    defaults[field_name] = "2025-01-01"
                elif field_type == "datetime":
                    defaults[field_name] = "2025-01-01 00:00:00"
                elif field_type == "many2one":
                    # For many2one, we'd need to create or find a record
                    # Skip for now as it's more complex
                    pass

        cls._cache[cache_key] = defaults.copy()
        return defaults

    @classmethod
    def create_test_partner(cls, env, name, **kwargs):
        """Create a test partner with all required fields filled.

        Args:
            env: Odoo environment
            name: Partner name
            **kwargs: Additional field values to override defaults

        Returns:
            res.partner: Created partner record
        """
        # Get required defaults
        defaults = cls.get_required_defaults(env, "res.partner")

        # Build values dict
        values = defaults.copy()
        values["name"] = name

        # Override with provided values
        values.update(kwargs)

        return env["res.partner"].create(values)

    @classmethod
    def create_test_user(cls, env, name, login, **kwargs):
        """Create a test user with all required fields filled.

        Args:
            env: Odoo environment
            name: User name
            login: User login
            **kwargs: Additional field values to override defaults

        Returns:
            res.users: Created user record
        """
        # Check if we need to handle autopost_bills
        partner_has_autopost_bills = False
        try:
            partner_fields = env["res.partner"]._fields
            if "autopost_bills" in partner_fields:
                partner_has_autopost_bills = True
        except (AttributeError, KeyError):
            # AttributeError: env["res.partner"] might not exist
            # KeyError: _fields might not be accessible
            pass

        # If autopost_bills exists and we need to set it, create partner first
        if partner_has_autopost_bills and "partner_id" not in kwargs:
            # Create partner with autopost_bills set
            partner_vals = {
                "name": name,
                "email": kwargs.get("email", ""),
                "autopost_bills": "ask",  # Safe default
            }
            # Get partner defaults
            partner_defaults = cls.get_required_defaults(env, "res.partner")
            for key, value in partner_defaults.items():
                if key not in partner_vals:
                    partner_vals[key] = value

            partner = env["res.partner"].create(partner_vals)
            kwargs["partner_id"] = partner.id

        # Get required defaults for user
        values = cls.get_required_defaults(env, "res.users")

        # Set required fields
        values["name"] = name
        values["login"] = login

        # Override with provided values
        values.update(kwargs)

        # Create user
        return env["res.users"].create(values)


# Convenience functions
def get_required_defaults(env, model_name):
    """Get required field defaults for a model."""
    return TestHelpers.get_required_defaults(env, model_name)


def create_test_partner(env, name, **kwargs):
    """Create a test partner with all required fields filled."""
    return TestHelpers.create_test_partner(env, name, **kwargs)


def create_test_user(env, name, login, **kwargs):
    """Create a test user with all required fields filled."""
    return TestHelpers.create_test_user(env, name, login, **kwargs)


def create_test_config_settings(env, **kwargs):
    """Create test config settings with all required fields filled.

    This is specifically designed to handle res.config.settings which
    can have required fields from many different modules.
    """
    Settings = env["res.config.settings"]

    # Get all fields and their info
    fields_info = Settings.fields_get()

    # Get default values
    defaults = Settings.default_get(list(fields_info.keys()))

    # Start with defaults
    values = defaults.copy()

    # Add safe defaults for any missing required fields
    for field_name, field_info in fields_info.items():
        if field_info.get("required") and field_name not in values:
            field_type = field_info.get("type")

            # Skip computed and readonly fields
            if field_info.get("compute") or field_info.get("readonly"):
                continue

            # Provide safe defaults based on field type
            if field_type == "boolean":
                values[field_name] = False
            elif field_type == "integer":
                values[field_name] = 0
            elif field_type == "float":
                values[field_name] = 0.0
            elif field_type == "char":
                values[field_name] = ""
            elif field_type == "text":
                values[field_name] = ""
            elif field_type == "selection":
                # Get the first available option
                selection = field_info.get("selection", [])
                if selection and isinstance(selection, list) and selection[0]:
                    values[field_name] = selection[0][0]
            elif field_type == "many2one":
                # Try to find a default record
                comodel = field_info.get("relation")
                if comodel:
                    try:
                        # Look for a default or first record
                        default_rec = env[comodel].search([], limit=1)
                        if default_rec:
                            values[field_name] = default_rec.id
                    except Exception:
                        pass

    # Override with provided values
    values.update(kwargs)

    # Create settings
    return Settings.create(values)
