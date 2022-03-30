from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.FIRST_OBJECT_INDEX = 0
        cls.author_user = User.objects.create_user(username='author')
        cls.follower_user = User.objects.create_user(username='follower')
        cls.non_follower_user = User.objects.create_user(username='non_follower')
        cls.first_post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )
        Follow.objects.create(
            user=cls.follower_user,
            author=cls.author_user,
        )

    def setUp(self):
        self.author_client = Client()
        self.follower_client = Client()
        self.non_follower_client = Client()
        self.follower_client.force_login(self.follower_user)
        self.non_follower_client.force_login(self.non_follower_user)

    def test_autorized_user_can_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей
        """
        response = self.non_follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author_user.username}
        ))
        self.assertTrue(
            Follow.objects.filter(user__exact=self.non_follower_user).filter(
                author__exact=self.author_user
            ))

    def test_autorized_user_can_unfollow(self):
        """Авторизованный пользователь может удалять из подписок других
        пользователей
        """
        response = self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author_user.username}
        ))
        self.assertEqual(
            Follow.objects.count(), 0)

    def test_new_authors_post_appears_in_followers_feed(self):
        """Новая запись автора появляется в ленте тех, кто на
        него подписан
        """
        response_before_new_post = self.follower_client.get(reverse(
            'posts:follow_index'
        ))
        second_post = Post.objects.create(
            author=self.author_user,
            text='Тестовый2пост2Тестовый2пост2Тестовый2пост',
        )
        response_after_new_post = self.follower_client.get(reverse(
            'posts:follow_index'
        ))
        self.assertNotEqual(
            response_before_new_post.content,
            response_after_new_post.content
        )
        first_object = response_after_new_post.context['page_obj'][
            self.FIRST_OBJECT_INDEX
        ]
        self.assertEqual(first_object.text, second_post.text)

    def test_new_authors_post_doesnt_appear_in_non_followers_feed(self):
        """Новая запись автора не появляется в ленте тех,
        кто не подписан
        """
        response_before_new_post = self.non_follower_client.get(reverse(
            'posts:follow_index'
        ))
        second_post = Post.objects.create(
            author=self.author_user,
            text='Тестовый2пост2Тестовый2пост2Тестовый2пост',
        )
        response_after_new_post = self.non_follower_client.get(reverse(
            'posts:follow_index'
        ))
        self.assertEqual(
            response_before_new_post.content,
            response_after_new_post.content
        )
