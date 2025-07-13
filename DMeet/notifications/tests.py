from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Notification, EmailTemplate, EmailLog

User = get_user_model()


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.notification = Notification.objects.create(
            recipient=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='SYSTEM'
        )
    
    def test_notification_creation(self):
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.title, 'Test Notification')
        self.assertFalse(self.notification.is_read)
    
    def test_mark_as_read(self):
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)


class EmailTemplateTest(TestCase):
    def test_email_template_creation(self):
        template = EmailTemplate.objects.create(
            name='welcome_email',
            subject='Welcome to DMeeet!',
            html_content='<h1>Welcome!</h1>',
            text_content='Welcome!'
        )
        
        self.assertEqual(template.name, 'welcome_email')
        self.assertTrue(template.is_active)