# -*- coding: utf-8 -*-
import logging
import traceback

from pyrevit import DB

logger = logging.getLogger(__name__)

# ElementId compatibility for Revit 2024+ (IntegerValue -> Value)
try:
    from pyrevit.compat import get_elementid_value_func

    _get_eid_value = get_elementid_value_func()
except (ImportError, Exception):
    # Fallback for environments without compat module
    def _get_eid_value(eid):
        try:
            return eid.Value
        except AttributeError:
            return eid.IntegerValue


def get_element_id_value(element_id):
    """Get numeric value from ElementId, compatible with Revit 2024+"""
    try:
        return int(_get_eid_value(element_id))
    except Exception:
        return -1


def normalize_string(text):
    """Safely normalize string values"""
    if text is None:
        return "Unnamed"
    return str(text).strip()


def get_element_name(element):
    """
    Get the name of a Revit element.
    Useful for both FamilySymbol and other elements.
    """
    try:
        return element.Name
    except AttributeError:
        return DB.Element.Name.__get__(element)


def find_family_symbol_safely(doc, target_family_name, target_type_name=None):
    """
    Safely find a family symbol by name
    """
    try:
        collector = DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol)

        for symbol in collector:
            if symbol.Family.Name == target_family_name:
                if not target_type_name or symbol.Name == target_type_name:
                    return symbol
        return None
    except Exception as e:
        logger.error("Error finding family symbol: %s", str(e))
        return None
