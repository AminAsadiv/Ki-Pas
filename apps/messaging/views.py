from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from .models import Conversation, Message, MessageReadReceipt
from apps.accounts.models import User
from apps.social.models import Friendship


def _friend_ids(user):
    pairs = Friendship.objects.filter(
        Q(sender=user, status='accepted') | Q(receiver=user, status='accepted')
    ).values_list('sender_id', 'receiver_id')
    ids = set()
    for s, r in pairs:
        ids.add(str(s)); ids.add(str(r))
    ids.discard(str(user.id))
    return ids


def _conv_context(request, conversations, active_conv=None):
    conv_data = []
    for conv in conversations:
        if conv.is_group:
            other = None
        else:
            other = conv.participants.exclude(pk=request.user.pk).select_related('profile').first()
        last_msg = conv.messages.filter(is_deleted=False).order_by('-created_at').first()
        unread = conv.messages.filter(is_deleted=False).exclude(sender=request.user).exclude(
            id__in=MessageReadReceipt.objects.filter(user=request.user).values('message_id')
        ).count()
        conv_data.append({
            'conv': conv,
            'other': other,
            'last_msg': last_msg,
            'unread': unread,
            'is_active': active_conv and conv.id == active_conv.id,
        })
    return conv_data


class MessagesView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'participants__profile').order_by('-updated_at')

        conv_data = _conv_context(request, conversations)
        friends = User.objects.filter(id__in=_friend_ids(request.user)).select_related('profile')[:20]

        return render(request, 'messages/messages.html', {
            'conv_data': conv_data,
            'friends': friends,
        })


class ConversationView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, conversation_id):
        active_conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        messages_qs = active_conv.messages.filter(
            is_deleted=False
        ).select_related('sender', 'sender__profile', 'reply_to', 'reply_to__sender').order_by('created_at')

        unread_msgs = messages_qs.exclude(sender=request.user).exclude(
            id__in=MessageReadReceipt.objects.filter(user=request.user).values('message_id')
        )
        if unread_msgs.exists():
            MessageReadReceipt.objects.bulk_create(
                [MessageReadReceipt(message=m, user=request.user) for m in unread_msgs],
                ignore_conflicts=True,
            )

        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'participants__profile').order_by('-updated_at')

        conv_data = _conv_context(request, conversations, active_conv)
        other_user = None
        group_members = []
        if active_conv.is_group:
            group_members = list(active_conv.participants.select_related('profile').exclude(pk=request.user.pk))
        else:
            other_user = active_conv.participants.exclude(pk=request.user.pk).select_related('profile').first()

        friends = User.objects.filter(id__in=_friend_ids(request.user)).select_related('profile')[:20]

        from django.utils import timezone as tz
        from datetime import timedelta
        today = tz.now().date()
        yesterday = today - timedelta(days=1)

        return render(request, 'messages/messages.html', {
            'conv_data': conv_data,
            'active_conversation': active_conv,
            'messages': messages_qs,
            'other_user': other_user,
            'group_members': group_members,
            'friends': friends,
            'today': today.strftime('%Y-%m-%d'),
            'yesterday': yesterday.strftime('%Y-%m-%d'),
        })


class NewConversationView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, username):
        other_user = get_object_or_404(User, username=username)
        if other_user == request.user:
            return redirect('messaging:inbox')
        existing = Conversation.objects.filter(
            participants=request.user, is_group=False
        ).filter(participants=other_user).first()
        if existing:
            return redirect('messaging:conversation', conversation_id=existing.id)
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other_user)
        return redirect('messaging:conversation', conversation_id=conv.id)


class CreateGroupView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        name = request.POST.get('name', '').strip()
        member_ids = request.POST.getlist('members')
        if not name:
            return JsonResponse({'error': 'Group name is required'}, status=400)

        friend_ids = _friend_ids(request.user)
        valid_ids = [uid for uid in member_ids if uid in friend_ids]
        if not valid_ids:
            return JsonResponse({'error': 'Select at least one friend'}, status=400)

        conv = Conversation.objects.create(is_group=True, name=name, created_by=request.user)
        users_to_add = list(User.objects.filter(id__in=valid_ids))
        conv.participants.add(request.user, *users_to_add)
        Message.objects.create(
            conversation=conv, sender=request.user,
            content=f'{request.user.username} created the group "{name}"',
        )
        return JsonResponse({'redirect': f'/messages/{conv.id}/'})


class GroupSettingsView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user, is_group=True)
        action = request.POST.get('action')

        if action == 'rename':
            name = request.POST.get('name', '').strip()
            if name:
                conv.name = name
                conv.save(update_fields=['name'])
                Message.objects.create(
                    conversation=conv, sender=request.user,
                    content=f'{request.user.username} renamed the group to "{name}"',
                )
            return JsonResponse({'ok': True, 'name': conv.name})

        if action == 'add_member':
            uid = request.POST.get('user_id')
            if uid in _friend_ids(request.user):
                user_to_add = get_object_or_404(User, id=uid)
                conv.participants.add(user_to_add)
                Message.objects.create(
                    conversation=conv, sender=request.user,
                    content=f'{request.user.username} added {user_to_add.username} to the group',
                )
            return JsonResponse({'ok': True})

        if action == 'leave':
            conv.participants.remove(request.user)
            Message.objects.create(
                conversation=conv, sender=request.user,
                content=f'{request.user.username} left the group',
            )
            return JsonResponse({'redirect': '/messages/'})

        return JsonResponse({'error': 'Unknown action'}, status=400)


class GroupEventRedirectView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user, is_group=True)
        usernames = ','.join(
            conv.participants.exclude(pk=request.user.pk).values_list('username', flat=True)
        )
        return redirect(f'/events/create/?group={conv.id}&cohosts={usernames}')


class SendMessageView(LoginRequiredMixin, View):
    """HTTP fallback for sending a message — also broadcasts via channel layer."""
    login_url = '/accounts/login/'

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'empty'}, status=400)

        reply_to = None
        reply_to_id = request.POST.get('reply_to_id')
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, conversation=conv)
            except Message.DoesNotExist:
                pass

        msg = Message.objects.create(
            conversation=conv,
            sender=request.user,
            content=content,
            reply_to=reply_to,
        )
        from django.utils import timezone as tz
        Conversation.objects.filter(id=conversation_id).update(updated_at=tz.now())

        avatar_url = ''
        try:
            if request.user.profile.avatar:
                avatar_url = request.user.profile.avatar.url
        except Exception:
            pass

        payload = {
            'id': msg.id,
            'content': msg.content,
            'sender_id': str(request.user.id),
            'sender_username': request.user.username,
            'sender_avatar': avatar_url,
            'created_at': msg.created_at.isoformat(),
            'message_type': msg.message_type,
            'reply_to': {
                'id': reply_to.id,
                'content': reply_to.content[:80],
                'sender_username': reply_to.sender.username,
            } if reply_to else None,
        }

        # Broadcast via channel layer so all WS clients receive it too
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        try:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'chat_{conversation_id}',
                {'type': 'chat_message', 'message': payload},
            )
        except Exception:
            pass

        return JsonResponse({'ok': True, 'message': payload})
