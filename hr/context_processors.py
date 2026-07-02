from .models import Notification


def notification_count(request):
    if not request.user.is_authenticated:
        return {'unread_notification_count': 0}
    try:
        if request.user.role.role == 'HR':
            count = Notification.objects.filter(is_read=False).count()
            return {'unread_notification_count': count}
    except Exception:
        pass
    return {'unread_notification_count': 0}
