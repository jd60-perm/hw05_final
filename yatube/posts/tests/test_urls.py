from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_user = User.objects.create_user(username='auth1')
        cls.user_for_redirect = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.first_post = Post.objects.create(
            author=cls.main_user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )
        cls.second_post = Post.objects.create(
            author=cls.user_for_redirect,
            text='15796126452792167519751794286582168198',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.main_user_client = Client()
        self.user_for_redirect_client = Client()
        self.main_user_client.force_login(self.main_user)
        self.user_for_redirect_client.force_login(self.user_for_redirect)

    def test_0_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.main_user.username}/': 'posts/profile.html',
            f'/posts/{self.first_post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.first_post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.main_user_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_exist_at_desired_location(self):
        """Страницы доступны пользователям с соответствующими правами."""
        guest_user_addresses = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.main_user.username}/',
            f'/posts/{self.first_post.pk}/'
        ]
        for address in guest_user_addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        main_user_addresses = [
            f'/posts/{self.first_post.pk}/edit/',
            '/create/'
        ]
        for address in main_user_addresses:
            with self.subTest(address=address):
                response = self.main_user_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница /posts/1/edit/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.first_post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{self.first_post.pk}/')

    def test_unexisting_url_exists_at_desired_location_authorized(self):
        """Страница /unexisting_page/ не доступна авторизованному
        пользователю.
        """
        response = self.main_user_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_non_author_on_post_info(self):
        """Страница /posts/1/edit/ перенаправит пользователя, не являющегося
        автором, на страницу поста.
        """
        response = self.user_for_redirect_client.get(
            f'/posts/{self.first_post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{self.first_post.pk}/')
