from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.FIRST_OBJECT_INDEX = 0
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_redirect_anonymous_on_login(self):
        """Форма add_comment перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}
        ), follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/')

    def test_created_comment_appears_on_post_page(self):
        """после успешной отправки комментарий появляется на странице поста"""
        comment_count = self.post.comments.count()
        form_data = {'text': 'Текст из формы', }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        comment = response.context['comments'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(self.post.comments.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
