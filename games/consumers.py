import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_{self.room_code}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        # Broadcast the incoming payload directly to everyone in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'data': data
            }
        )

    async def game_message(self, event):
        # Send message back to WebSocket
        await self.send(text_data=json.dumps(event['data']))
