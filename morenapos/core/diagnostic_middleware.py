"""
Middleware de diagnóstico para Azure App Service.
Captura cualquier excepción no manejada y la muestra en la respuesta HTTP
para poder diagnosticar errores 500.
"""
import traceback
import sys
import os


class DiagnosticMiddleware:
    """
    Middleware que captura excepciones y las muestra en la respuesta.
    Útil cuando DEBUG=True no funciona en Azure App Service.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Capturar el traceback completo
            tb_text = traceback.format_exc()
            
            # Escribir a stderr (aparece en los logs de Azure)
            print(f"DIAGNOSTIC ERROR: {e}", file=sys.stderr)
            print(tb_text, file=sys.stderr)
            
            # Devolver una respuesta HTML con el error
            from django.http import HttpResponse
            html = f"""<!DOCTYPE html>
<html>
<head><title>Error de diagnóstico</title></head>
<body style="font-family: monospace; padding: 20px; background: #f5f5f5;">
    <h1 style="color: #c00;">Error 500 - Diagnóstico</h1>
    <div style="background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
        <h2 style="color: #333;">{type(e).__name__}</h2>
        <p style="color: #666; font-size: 16px;"><strong>{str(e)}</strong></p>
        <hr>
        <h3>Traceback:</h3>
        <pre style="background: #f8f8f8; padding: 10px; overflow-x: auto; font-size: 12px; line-height: 1.5;">{tb_text}</pre>
    </div>
    <hr>
    <h3>Environment Variables (seguras):</h3>
    <pre style="background: #f8f8f8; padding: 10px; font-size: 12px;">
DEBUG: {os.environ.get('DJANGO_DEBUG', 'not set')}
ALLOWED_HOSTS: {os.environ.get('DJANGO_ALLOWED_HOSTS', 'not set')}
DB_ENGINE: {os.environ.get('DB_ENGINE', 'not set')}
DB_HOST: {os.environ.get('DB_HOST', 'not set')}
DB_NAME: {os.environ.get('DB_NAME', 'not set')}
DB_USER: {os.environ.get('DB_USER', 'not set')}
DB_DRIVER: {os.environ.get('DB_DRIVER', 'not set')}
    </pre>
</body>
</html>"""
            return HttpResponse(html, status=500, content_type='text/html; charset=utf-8')
