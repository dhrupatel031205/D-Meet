from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users with different roles
        self.user = User.objects.create_user(
            username='testuser',
            email='user@example.com',
            password='testpass123',
            role='USER'
        )
        
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            role='ORGANIZER'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='ADMIN'
        )
    
    def test_user_dashboard_access(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:user_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_organizer_dashboard_access(self):
        self.client.login(username='organizer', password='testpass123')
        response = self.client.get(reverse('dashboard:organizer_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_dashboard_access(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_cannot_access_admin_dashboard(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_dashboard_redirect_based_on_role(self):
        # Test admin redirect
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:user_dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # Test organizer redirect
        self.client.login(username='organizer', password='testpass123')
        response = self.client.get(reverse('dashboard:user_dashboard'))
        self.assertEqual(response.status_code, 302)