"""
Minimal test to isolate the API issue
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


@csrf_exempt
@require_POST
def minimal_json_test(request):
    """Minimal test without any API framework"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        # Parse JSON
        data = json.loads(request.body)
        json_data = data.get('data', '')
        
        # Simple JSON formatting
        try:
            parsed = json.loads(json_data)
            formatted = json.dumps(parsed, indent=2)
            return JsonResponse({
                'success': True,
                'result': formatted,
                'stats': {
                    'input_size': len(json_data),
                    'output_size': len(formatted)
                }
            })
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)
