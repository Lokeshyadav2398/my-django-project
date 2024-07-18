from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer
from django.db.models import Q
from datetime import datetime, timedelta

class UserSignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email').lower()
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):
            return Response(UserSerializer(user).data)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query', '').lower()
        return User.objects.filter(Q(email__iexact=query) | Q(username__icontains=query))[:10]

class FriendRequestView(generics.ListCreateAPIView):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(to_user=self.request.user, status='pending')

    def perform_create(self, serializer):
        from_user = self.request.user
        to_user_id = self.request.data.get('to_user')
        to_user = User.objects.get(id=to_user_id)

        # Limit to 3 friend requests per minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_requests = FriendRequest.objects.filter(from_user=from_user, timestamp__gte=one_minute_ago)
        if recent_requests.count() >= 3:
            raise serializers.ValidationError("You can't send more than 3 friend requests per minute.")

        serializer.save(from_user=from_user, to_user=to_user)

class FriendRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request_id = request.data.get('id')
        action = request.data.get('action')
        friend_request = FriendRequest.objects.filter(id=request_id, to_user=request.user).first()
        if friend_request:
            if action == 'accept':
                friend_request.status = 'accepted'
            elif action == 'reject':
                friend_request.status = 'rejected'
            friend_request.save()
            return Response({'status': 'success'})
        return Response({'error': 'Invalid Request'}, status=status.HTTP_400_BAD_REQUEST)

class FriendListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friends = User.objects.filter(
            Q(sent_requests__to_user=user, sent_requests__status='accepted') |
            Q(received_requests__from_user=user, received_requests__status='accepted')
        ).distinct()
        return friends
