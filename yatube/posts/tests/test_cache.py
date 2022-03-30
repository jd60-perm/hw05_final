from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.FIRST_OBJECT_INDEX = 0
        cls.user = User.objects.create_user(username='auth')
        cls.first_post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )
        cls.second_post = Post.objects.create(
            author=cls.user,
            text='Тестовый2пост2Тестовый2пост2Тестовый2пост',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_post_in_cache_until_clean(self):
        """При удалении поста из базы, он остаётся на главной странице
        до тех пор, пока кэш не будет очищен принудительно."""
        response_before_delete = self.guest_client.get('/')
        self.second_post.delete()
        response_after_delete = self.guest_client.get('/')
        self.assertEqual(
            response_before_delete.content,
            response_after_delete.content
        )
        cache.clear()
        response_after_cacheclear = self.guest_client.get('/')
        self.assertNotEqual(
            response_before_delete.content,
            response_after_cacheclear.content
        )
        first_object = response_after_cacheclear.context[
            'page_obj'
        ][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            'Тестовый пост Тестовый пост Тестовый пост'
        )
