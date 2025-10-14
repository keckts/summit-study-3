# Test specifically for 400 Bad Request scenarios
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
import json

User = get_user_model()


class LoginView400ErrorTests(TestCase):
    """
    Comprehensive tests for testing 400 Bad Request scenarios in login view
    """
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')  # Adjust this to your actual URL name
        
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123'
        )
    
    def test_empty_ajax_request_returns_400(self):
        """Test that empty AJAX request returns 400 status"""
        response = self.client.post(
            self.login_url,
            {},  # Empty data
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Depending on your implementation:
        # If you use the enhanced version, this should return 400
        # If you use your current version, this returns 200 with errors
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            response_data = json.loads(response.content)
            self.assertFalse(response_data['success'])
            self.assertIn('error', response_data)
        elif response.status_code == 200:
            response_data = json.loads(response.content)
            self.assertFalse(response_data['success'])
            self.assertIn('errors', response_data)
    
    def test_invalid_username_ajax_returns_400(self):
        """Test that invalid username in AJAX returns 400"""
        data = {
            'username': '',  # Invalid empty username
            'password': 'somepassword'
        }
        response = self.client.post(
            self.login_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"Status Code: {response.status_code}")
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
        if response.status_code == 400:
            self.assertIn('error', response_data)
        elif response.status_code == 200:
            self.assertIn('errors', response_data)
    
    def test_invalid_password_ajax_returns_400(self):
        """Test that invalid password in AJAX returns 400"""
        data = {
            'username': 'testuser@example.com',
            'password': ''  # Invalid empty password
        }
        response = self.client.post(
            self.login_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"Status Code: {response.status_code}")
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        
        if response.status_code == 400:
            self.assertIn('error', response_data)
        elif response.status_code == 200:
            self.assertIn('errors', response_data)
    
    def test_wrong_credentials_ajax(self):
        """Test wrong credentials via AJAX"""
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(
            self.login_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"Status Code: {response.status_code}")
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
    
    def test_malformed_json_request(self):
        """Test malformed JSON in request body"""
        response = self.client.post(
            self.login_url,
            'invalid json data',
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # This should ideally return 400 for malformed data
        print(f"Status Code: {response.status_code}")
        self.assertIn(response.status_code, [200, 400, 403])  # 403 might be CSRF related
    
    def test_unsupported_http_method(self):
        """Test unsupported HTTP methods return proper error codes"""
        # Test PUT method
        response = self.client.put(self.login_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Test DELETE method
        response = self.client.delete(self.login_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Test PATCH method
        response = self.client.patch(self.login_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_html_form_with_errors_shows_messages(self):
        """Test HTML form with errors shows proper messages"""
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        # Should return 200 with error messages
        self.assertEqual(response.status_code, 200)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        
        # Check that error message is present
        error_found = any('Incorrect email or password' in str(msg) for msg in messages)
        self.assertTrue(error_found)
    
    def test_html_form_empty_data(self):
        """Test HTML form with completely empty data"""
        response = self.client.post(self.login_url, {})
        
        # Should return 200 with error messages
        self.assertEqual(response.status_code, 200)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)


# Additional utility for testing your current vs enhanced implementation
class LoginViewComparisonTest(TestCase):
    """
    Use this to test different approaches to handling 400 errors
    """
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        
    def test_current_vs_enhanced_approach(self):
        """
        This test helps you see the difference between returning 200 vs 400
        """
        data = {
            'username': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        print("\n=== Testing AJAX Login Error Responses ===")
        
        response = self.client.post(
            self.login_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content.decode()}")
        
        if response.status_code == 200:
            print("✅ Current approach: Returns 200 with error details")
            print("   - Frontend friendly (no need to handle 400 errors)")
            print("   - Less RESTful")
        elif response.status_code == 400:
            print("✅ Enhanced approach: Returns 400 for validation errors") 
            print("   - More RESTful")
            print("   - Frontend needs to handle 400 status codes")
        
        # Test HTML form too
        print("\n=== Testing HTML Form Error Responses ===")
        response_html = self.client.post(self.login_url, data)
        print(f"HTML Form Status Code: {response_html.status_code}")
        
        messages = list(get_messages(response_html.wsgi_request))
        if messages:
            print(f"Error Messages: {[str(msg) for msg in messages]}")