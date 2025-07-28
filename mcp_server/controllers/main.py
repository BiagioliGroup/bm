"""Main REST API controller for MCP Server."""

import logging
from datetime import datetime

from odoo import http
from odoo.http import request

from . import auth, response_utils, utils
from .rate_limiting import rate_limit

_logger = logging.getLogger(__name__)


class McpAPIController(http.Controller):
    _name = "mcp.api.controller"

    @http.route("/mcp/health", type="http", auth="none", methods=["GET"], csrf=False)
    def health_check(self, **kwargs):
        """
        Health Check Endpoint

        Path: /mcp/health
        Method: GET
        Auth: None required
        Description: Check if MCP server is running properly
        Response: Basic server status and version information
        """
        if not utils.is_mcp_enabled():
            return response_utils.error_response(
                message="MCP Server is disabled globally.",
                code="E503",
                status=503,
            )

        mcp_server_version = utils.get_mcp_server_version()
        data = {
            "status": "ok",
            "mcp_server_version": mcp_server_version,
        }
        return response_utils.success_response(data)

    @http.route("/mcp/system/info", type="http", auth="none", methods=["GET"], csrf=False)
    @auth.require_api_key
    @rate_limit
    def system_info(self, **kwargs):
        """
        Database Information Endpoint
        Path: /mcp/system/info
        Method: GET
        Auth: API key required
        Description: Get database and MCP server information
        Response: DB name, Odoo version, language, timezone, enabled models count, etc.
        """
        if not utils.is_mcp_enabled():
            return response_utils.error_response(message="MCP Server is disabled globally.", code="E503", status=503)

        # Use the authenticated user's environment
        user = kwargs.get("user")
        if user:
            env = request.env(user=user.id)
        else:
            env = request.env

        system_info_data = utils.get_system_info(env)
        return response_utils.success_response(system_info_data)

    @http.route("/mcp/auth/validate", type="http", auth="none", methods=["GET"], csrf=False)
    @auth.require_api_key
    @rate_limit
    def validate_auth(self, **kwargs):
        """
        API Key Validation Endpoint
        Path: /mcp/auth/validate
        Method: GET
        Auth: API key required
        Description: Validate if API key is valid
        Response: Confirmation of validity and associated user ID
        """
        if not utils.is_mcp_enabled():
            return response_utils.error_response(message="MCP Server is disabled globally.", code="E503", status=503)

        user = kwargs.get("user")
        # The require_api_key decorator already validates the key.
        # If we reach here, the key is valid and user is in kwargs.
        if user:
            data = {
                "valid": True,
                "user_id": user.id,
            }
            return response_utils.success_response(data)
        else:
            # This case should ideally not be reached if require_api_key works as expected
            return response_utils.error_response("API key validation failed unexpectedly.", "E500", status=500)

    @http.route("/mcp/models", type="http", auth="none", methods=["GET"], csrf=False)
    @auth.require_api_key
    @rate_limit
    def get_models(self, **kwargs):
        """
        Get Enabled Models Endpoint
        Path: /mcp/models
        Method: GET
        Auth: API key required
        Description: Get all MCP-enabled models
        Response: List of models with technical and display names
        """
        if not utils.is_mcp_enabled():
            return response_utils.error_response(message="MCP Server is disabled globally.", code="E503", status=503)

        # Use the authenticated user's environment
        user = kwargs.get("user")
        if user:
            env = request.env(user=user.id)
        else:
            env = request.env

        enabled_models = utils.get_enabled_models(env)
        data = {"models": enabled_models}
        return response_utils.success_response(data)

    @http.route(
        "/mcp/models/<string:model>/access",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    @auth.require_api_key
    @rate_limit
    def get_model_access(self, model, **kwargs):
        """
        Get Model Access Information Endpoint
        Path: /mcp/models/{model}/access
        Method: GET
        Auth: API key required
        Description: Check if model is MCP-enabled and get allowed operations
        Response: Model enablement status and allowed operations
        """
        start_time = datetime.now()

        if not utils.is_mcp_enabled():
            return response_utils.error_response(message="MCP Server is disabled globally.", code="E503", status=503)

        # Use the authenticated user's environment
        user = kwargs.get("user")
        if user:
            env = request.env(user=user.id)
        else:
            env = request.env

        # Validate and sanitize model name
        try:
            model_technical_name = utils.sanitize_model_name(model)
        except ValueError as e:
            return response_utils.error_response(
                message=str(e),
                code="E400",
                status=400,
            )

        # Check if the model itself exists in ir.model to give a more specific error if not.
        ir_model = env["ir.model"].sudo().search([("model", "=", model_technical_name)], limit=1)
        if not ir_model:
            # Log error only if we have a valid environment
            if env and hasattr(env, "__getitem__"):
                env["mcp.log"].sudo().log_error(
                    error_message=f"Model '{model_technical_name}' not found in Odoo instance.",
                    error_code="E404",
                    endpoint=request.httprequest.path,
                    model_name=model_technical_name,
                    operation="access",
                    user_id=user.id if user else None,
                    ip_address=request.httprequest.remote_addr,
                )
            return response_utils.error_response(
                message=f"Model '{model_technical_name}' not found in Odoo instance.",
                code="E404",
                status=404,
            )

        is_enabled = utils.is_model_mcp_enabled(env, model_technical_name)

        # Return 403 Forbidden if the model is not MCP-enabled
        if not is_enabled:
            # Log permission denied
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            env["mcp.log"].sudo().log_permission_denied(
                model_name=model_technical_name,
                operation="access",
                user_id=user.id if user else None,
                endpoint=request.httprequest.path,
                ip_address=request.httprequest.remote_addr,
                error_message=f"Model '{model_technical_name}' is not enabled for MCP access.",
            )
            return response_utils.error_response(
                message=f"Model '{model_technical_name}' is not enabled for MCP access.",
                code="E403",
                status=403,
            )

        # If enabled, get operations
        operations = utils.get_model_allowed_operations(env, model_technical_name)

        # Log successful model access
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        env["mcp.log"].sudo().log_model_access(
            model_name=model_technical_name,
            operation="access",
            user_id=user.id if user else None,
            endpoint=request.httprequest.path,
            http_method=request.httprequest.method,
            duration_ms=duration_ms,
            ip_address=request.httprequest.remote_addr,
        )

        data = {
            "model": model_technical_name,
            "enabled": is_enabled,
            "operations": operations,
        }
        return response_utils.success_response(data)
