from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from .models import Conversation, Message


class ConversationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        convs = Conversation.objects.filter(participants=request.user).prefetch_related('participants__profile').order_by('-updated_at')
        result = []
        for c in convs:
            other = c.participants.exclude(pk=request.user.pk).first()
            last = c.messages.order_by('-created_at').first()
            result.append({
                'id': c.pk, 'is_group': c.is_group, 'name': c.name,
                'other_user': {'username': other.username, 'id': str(other.id)} if other else None,
                'last_message': {'content': last.content, 'created_at': last.created_at.isoformat()} if last else None,
                'unread_count': c.messages.filter(is_read=False).exclude(sender=request.user).count(),
            })
        return Response(result)


class ConversationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk, participants=request.user)
        msgs = conv.messages.select_related('sender').order_by('-created_at')[:50]
        return Response([{
            'id': m.pk, 'content': m.content, 'message_type': m.message_type,
            'sender': m.sender.username, 'created_at': m.created_at.isoformat(), 'is_read': m.is_read,
        } for m in reversed(list(msgs))])


class MessageListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk, participants=request.user)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'detail': 'Message cannot be empty'}, status=400)
        msg = Message.objects.create(conversation=conv, sender=request.user, content=content)
        conv.updated_at = msg.created_at
        conv.save(update_fields=['updated_at'])
        return Response({'id': msg.pk, 'content': msg.content, 'created_at': msg.created_at.isoformat()}, status=201)


class StartConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({'detail': 'Cannot message yourself'}, status=400)
        existing = Conversation.objects.filter(participants=request.user, is_group=False).filter(participants=target).first()
        if existing:
            return Response({'id': existing.pk, 'existing': True})
        conv = Conversation.objects.create(is_group=False)
        conv.participants.set([request.user, target])
        return Response({'id': conv.pk, 'existing': False}, status=201)
