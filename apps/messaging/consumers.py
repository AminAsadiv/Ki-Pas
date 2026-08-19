import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
        if not await self.is_participant(user):
            await self.close()
            return
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_online',
            'user_id': str(user.id),
            'username': user.username,
            'online': True,
        })

    async def disconnect(self, close_code):
        user = self.scope.get('user')
        if user and user.is_authenticated:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'user_online',
                'user_id': str(user.id),
                'username': user.username,
                'online': False,
            })
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'message.new')
        user = self.scope['user']

        if msg_type == 'message.new':
            content = data.get('content', '').strip()
            if not content:
                return
            message = await self.save_message(user, content, data.get('reply_to_id'))
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message': message,
            })
        elif msg_type == 'typing.start':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing_indicator',
                'user_id': str(user.id),
                'username': user.username,
                'typing': True,
            })
        elif msg_type == 'typing.stop':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing_indicator',
                'user_id': str(user.id),
                'username': user.username,
                'typing': False,
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'message.new', 'message': event['message']}))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'typing': event['typing'],
        }))

    async def user_online(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'username': event['username'],
            'online': event['online'],
        }))

    @database_sync_to_async
    def is_participant(self, user):
        from .models import Conversation
        return Conversation.objects.filter(id=self.conversation_id, participants=user).exists()

    @database_sync_to_async
    def save_message(self, user, content, reply_to_id=None):
        from .models import Message, Conversation
        conversation = Conversation.objects.get(id=self.conversation_id)
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, conversation=conversation)
            except Message.DoesNotExist:
                pass
        msg = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content,
            reply_to=reply_to,
        )
        Conversation.objects.filter(id=self.conversation_id).update(updated_at=timezone.now())

        avatar_url = ''
        try:
            if user.profile.avatar:
                avatar_url = user.profile.avatar.url
        except Exception:
            pass

        reply_data = None
        if reply_to:
            reply_data = {
                'id': reply_to.id,
                'content': reply_to.content[:80],
                'sender_username': reply_to.sender.username,
            }

        return {
            'id': msg.id,
            'content': msg.content,
            'sender_id': str(user.id),
            'sender_username': user.username,
            'sender_avatar': avatar_url,
            'created_at': msg.created_at.isoformat(),
            'message_type': msg.message_type,
            'reply_to': reply_data,
        }
