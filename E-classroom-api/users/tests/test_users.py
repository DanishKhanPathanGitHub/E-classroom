from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

CREATE_USER_URL = reverse('user:create-user')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')
ME_URL_UPDATE = reverse('user:me-update')

def generate_test_image(name='test.jpg'):
    """Creates a simple test image file."""
    image = Image.new("RGB", (10, 10), color="red")  
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)
    return SimpleUploadedFile(name, image_io.read(), content_type="image/jpeg")

def create_user(**params):
    default = {
        'email':'test@example.com',
        'password': 'testpass123',
        'username':'Test Name',
        'role':1,
        "profile_pic": generate_test_image()
    }
    return get_user_model().objects.create_user(**default)

class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        payload = {
            'email':'test@example.com',
            'password': 'testpass123',
            'confirm_password':'testpass123',
            'username':'Test Name',
            'profile_pic': generate_test_image(),
            'role':1
        }
        res = self.client.post(CREATE_USER_URL, payload)
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.filter(email=payload['email']).first()
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

        

    def test_user_with_errors(self):
        create_user()

        payload = {'email':'test@example.com', 'password': 'testpass123', 'username':'Test Name 2'}
        req_with_same_email = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(req_with_same_email.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {'email':'test2@example.com', 'password': 'testpas', 'username':'Test Name 2'}
        req_with_bad_password = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(req_with_bad_password.status_code, status.HTTP_400_BAD_REQUEST)


    def test_token_create_for_user(self):
        user = create_user()
        user.is_active = True
        user.save()
        
        payload = {
            'email':'test@example.com',
            'password':'testpass123'
        }
        res = self.client.post(TOKEN_URL, payload)
        print('res data:', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', res.data)
        self.assertIn('refresh_token', res.data)

    def retrive_user_unauthorized(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass",
            username="Test name",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


    def test_retrieve_profile_success(self):

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], self.user.username)
        self.assertEqual(res.data['email'], self.user.email)
        self.assertEqual(res.data['role'], 1)
        self.assertIn('profile_pic', res.data)

    def test_user_profile_update(self):

        payload = {
            "username":"updated name",
            "profile_pic": generate_test_image(name='test-update.jpg')
        }
        res = self.client.patch(ME_URL_UPDATE, payload, format='multipart')
        print(res.content, res.data, res.json())
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.username, payload['username'])
        