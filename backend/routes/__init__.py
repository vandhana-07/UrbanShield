import datetime
from flask import jsonify

def make_response(data, source="mock", status_code=200):
    """
    Standardized success response envelope for all UrbanShield API endpoints.
    """
    return jsonify({
        "success": True,
        "data": data,
        "meta": {
            "source": source,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "version": "v1"
        }
    }), status_code


def make_error(code, message, details=None, status_code=400):
    """
    Standardized error response envelope for all UrbanShield API endpoints.
    """
    return jsonify({
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or []
        },
        "meta": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "version": "v1"
        }
    }), status_code
