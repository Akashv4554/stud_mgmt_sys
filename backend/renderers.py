from rest_framework.renderers import JSONRenderer

class StandardizedJSONRenderer(JSONRenderer):
    """
    Custom renderer to ensure all API responses have a consistent format.
    {
        "status": "success" | "error",
        "message": str,
        "data": dict | list
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        
        # Standard format
        status_text = "success" if response.status_code < 400 else "error"
        message = ""
        
        # Handle cases where data is already a message (e.g., error detail)
        if isinstance(data, dict):
            message = data.get('detail', data.get('message', ""))
            if 'detail' in data:
                del data['detail']
            if 'message' in data:
                del data['message']
        
        standardized_data = {
            "status": status_text,
            "message": message,
            "data": data
        }
        
        return super().render(standardized_data, accepted_media_type, renderer_context)
