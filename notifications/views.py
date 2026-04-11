from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


class MyNotificationsView(generics.ListAPIView):
    """Get all notifications for logged-in user"""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs       = Notification.objects.filter(recipient=self.request.user)
        unread   = self.request.query_params.get('unread')
        ntype    = self.request.query_params.get('type')
        if unread:
            qs = qs.filter(is_read=False)
        if ntype:
            qs = qs.filter(type=ntype)
        return qs


class MarkReadView(APIView):
    """Mark a single notification as read"""
    def patch(self, request, pk):
        try:
            notification         = Notification.objects.get(pk=pk, recipient=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Marked as read'})
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class MarkAllReadView(APIView):
    """Mark all notifications as read"""
    def patch(self, request):
        Notification.objects.filter(
            recipient = request.user,
            is_read   = False
        ).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})


class UnreadCountView(APIView):
    """Get count of unread notifications"""
    def get(self, request):
        count = Notification.objects.filter(
            recipient = request.user,
            is_read   = False
        ).count()
        return Response({'unread_count': count})


class DeleteNotificationView(APIView):
    """Delete a notification"""
    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.delete()
            return Response({'message': 'Deleted'})
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )