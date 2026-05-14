from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SignalingRoom
import random
import string
import json

def game_index(request):
    context = {
        'page_title': 'Mini Games Hub | LamGen Arcade',
        'games': [
            {
                'name': 'Reaction Test',
                'slug': 'reaction-test',
                'icon': 'bi bi-lightning-fill',
                'color': '#3EECD8',
                'short_desc': 'Test your reflexes against the clock. Fastest tap wins.'
            },
            {
                'name': 'Typing Duel',
                'slug': 'typing-duel',
                'icon': 'bi bi-keyboard-fill',
                'color': '#8B7FFF',
                'short_desc': 'Type as fast as you can to survive the word storm.'
            },
            {
                'name': 'Would You Rather',
                'slug': 'would-you-rather',
                'icon': 'bi bi-question-circle-fill',
                'color': '#FF5C7A',
                'short_desc': 'Choose between two impossible scenarios. See what others picked.'
            },
            {
                'name': 'Memory Flash',
                'slug': 'memory-flash',
                'icon': 'bi bi-grid-3x3-gap-fill',
                'color': '#F59E0B',
                'short_desc': 'Repeat the sequence. How far can your memory go?'
            },
            {
                'name': 'Roast Battle',
                'slug': 'roast-battle',
                'icon': 'bi bi-fire',
                'color': '#FFD700',
                'short_desc': 'The ultimate procedurally generated burn engine.'
            }
        ]
    }
    return render(request, 'games/index.html', context)

@csrf_exempt
def create_room(request):
    # Clean up old rooms (simple cleanup)
    from django.utils import timezone
    from datetime import timedelta
    SignalingRoom.objects.filter(created_at__lt=timezone.now() - timedelta(hours=1)).delete()
    
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    # Ensure unique code
    while SignalingRoom.objects.filter(code=code).exists():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
    SignalingRoom.objects.create(code=code)
    return JsonResponse({'code': code})

@csrf_exempt
def post_signal(request, code):
    try:
        room = SignalingRoom.objects.get(code=code)
        data = json.loads(request.body)
        
        if 'offer' in data: room.offer = data['offer']
        if 'answer' in data: room.answer = data['answer']
        
        # Append ICE candidates instead of overwriting
        if 'ice' in data:
            side = data.get('side') # 'host' or 'guest'
            current_ice = json.loads((room.host_ice if side == 'host' else room.guest_ice) or '[]')
            current_ice.append(data['ice'])
            if side == 'host':
                room.host_ice = json.dumps(current_ice)
            else:
                room.guest_ice = json.dumps(current_ice)
                
        room.save()
        return JsonResponse({'status': 'ok'})
    except SignalingRoom.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Room not found'}, status=404)

def get_signal(request, code):
    try:
        room = SignalingRoom.objects.get(code=code)
        return JsonResponse({
            'offer': room.offer,
            'answer': room.answer,
            'host_ice': json.loads(room.host_ice or '[]'),
            'guest_ice': json.loads(room.guest_ice or '[]'),
        })
    except SignalingRoom.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Room not found'}, status=404)
