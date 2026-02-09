# -*- coding: utf-8 -*-
"""Utility functions for MCP tools"""

import json


def format_response(response):
    """Helper function to format API responses consistently for MCP tools.

    Args:
        response: The response from a revit_get or revit_post call, can be dict or string

    Returns:
        str: Formatted string response suitable for MCP tool return values
    """
    if isinstance(response, dict):
        # Check for explicit error first
        if "error" in response:
            error_msg = response["error"]
            if "traceback" in response:
                return "Error: {}\n\nTraceback:\n{}".format(
                    error_msg, response["traceback"]
                )
            return "Error: {}".format(error_msg)

        # Check for different success patterns
        status = response.get("status", "").lower()
        health = response.get("health", "").lower()

        # Explicit success conditions
        is_success = (
            status == "success"
            or (status == "active" and health == "healthy")
            or (
                status == "active"
                and "revit_available" in response
                and response["revit_available"]
            )
        )

        if is_success:
            # For code execution responses, return just the output text
            if "output" in response:
                return response["output"]
            # For all other successful responses, return formatted JSON
            return json.dumps(response, indent=2, default=str)

        # No error key and no recognized success pattern — treat as success
        # This handles endpoints like model_info that return data without a status field
        return json.dumps(response, indent=2, default=str)
    else:
        # If response is already a string (error case from _revit_call)
        return str(response)
