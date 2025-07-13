from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserProfile, ConnectionRequest, UserConnection

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'USER')
        self.assertFalse(self.user.is_verified)
    
    def test_user_properties(self):
        self.assertFalse(self.user.is_organizer)
        self.assertFalse(self.user.is_admin)
        
        self.user.role = 'ORGANIZER'
        self.assertTrue(self.user.is_organizer)
        self.assertFalse(self.user.is_admin)
        
        self.user.role = 'ADMIN'
        self.assertTrue(self.user.is_organizer)
        self.assertTrue(self.user.is_admin)


class ConnectionTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_connection_request_creation(self):
        request = ConnectionRequest.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            message='Hello!'
        )
        
        self.assertEqual(request.from_user, self.user1)
        self.assertEqual(request.to_user, self.user2)
        self.assertFalse(request.accepted)
    
    def test_user_connection_creation(self):
        connection = UserConnection.objects.create(
            user1=self.user1,
            user2=self.user2
        )
        
        self.assertEqual(connection.user1, self.user1)
        self.assertEqual(connection.user2, self.user2)