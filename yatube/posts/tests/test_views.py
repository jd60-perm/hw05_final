import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import ModelChoiceField
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SAMPLE_POST_ID = 2
        cls.FIRST_OBJECT_INDEX = 0
        cls.PAGINATOR_1ST_PAGE_VOLUME = 10
        cls.PAGINATOR_2ND_page_VOLUME = 5
        cls.test_user = User.objects.create_user(username='auth')
        cls.empty_group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание 1',
        )
        cls.main_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        for i in range(1, 16):
            uploaded = SimpleUploadedFile(
                name=f'small_{i}.gif',
                content=small_gif,
                content_type='image/gif'
            )
            Post.objects.create(
                author=cls.test_user,
                text=f'{i}_Тестовый пост Тестовый пост Тестовый пост',
                group=cls.main_group,
                image=uploaded
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = [
            {'posts/index.html': reverse('posts:index')},
            {'posts/group_list.html': reverse('posts:group_list', kwargs={
                'slug': self.main_group.slug
            })},
            {'posts/profile.html': reverse('posts:profile', kwargs={
                'username': self.test_user.username
            })},
            {'posts/post_detail.html': reverse('posts:post_detail', kwargs={
                'post_id': self.SAMPLE_POST_ID
            })},
            {'posts/create_post.html': reverse('posts:post_edit', kwargs={
                'post_id': self.SAMPLE_POST_ID
            })},
            {'posts/create_post.html': reverse('posts:post_create')},
        ]
        for instance in templates_url_names:
            for template, reverse_name in instance.items():
                with self.subTest(template=template):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.SAMPLE_POST_ID}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        post_text = response.context['form'].initial['text']
        post_group = response.context['form'].initial['group']
        self.assertEqual(
            post_text,
            f'{self.SAMPLE_POST_ID}_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(post_group, self.main_group.pk)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': self.SAMPLE_POST_ID
            })
        )
        self.assertEqual(
            response.context['selected_post'].text,
            f'{self.SAMPLE_POST_ID}_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(
            response.context['selected_post'].author.username,
            self.test_user.username
        )
        self.assertEqual(
            response.context['selected_post'].group.title,
            self.main_group.title
        )
        self.assertEqual(
            response.context['selected_post'].image.name,
            f'posts/small_{self.SAMPLE_POST_ID}.gif'
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.test_user.username}
        ))
        first_object = response.context['page_obj'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            '15_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(str(first_object.author), self.test_user.username)
        self.assertEqual(str(first_object.group), self.main_group.title)
        self.assertEqual(first_object.image.name, 'posts/small_15.gif')

    def test_profile_first_page_paginator(self):
        """Корректная работа паджинатора на 1-й странице profile."""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.test_user.username}
        ))
        self.assertEqual(
            len(response.context['page_obj']),
            self.PAGINATOR_1ST_PAGE_VOLUME
        )

    def test_profile_second_page_paginator(self):
        """Корректная работа паджинатора на 2-й странице profile."""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.test_user.username}
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.PAGINATOR_2ND_page_VOLUME
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.main_group.slug}
        ))
        first_object = response.context['page_obj'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            '15_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(str(first_object.author), self.test_user.username)
        self.assertEqual(str(first_object.group), self.main_group.title)
        self.assertEqual(first_object.image.name, 'posts/small_15.gif')

    def test_group_list_first_page_paginator(self):
        """Корректная работа паджинатора на 1-й странице group_list."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.main_group.slug}
        ))
        self.assertEqual(
            len(response.context['page_obj']),
            self.PAGINATOR_1ST_PAGE_VOLUME
        )

    def test_group_list_second_page_paginator(self):
        """Корректная работа паджинатора на 2-й странице group_list."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.main_group.slug}
        ) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.PAGINATOR_2ND_page_VOLUME
        )

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            '15_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(str(first_object.author), self.test_user.username)
        self.assertEqual(str(first_object.group), self.main_group.title)
        self.assertEqual(first_object.image.name, 'posts/small_15.gif')

    def test_index_first_page_paginator(self):
        """Корректная работа паджинатора на 1-й странице index."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']),
            self.PAGINATOR_1ST_PAGE_VOLUME
        )

    def test_index_second_page_paginator(self):
        """Корректная работа паджинатора на 2-й странице index."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.PAGINATOR_2ND_page_VOLUME
        )

    def test_post_with_group_exists_on_index_page(self):
        """Пост с указанной группой появляется на главной странице."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            '15_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(str(first_object.author), self.test_user.username)
        self.assertEqual(str(first_object.group), self.main_group.title)

    def test_post_with_group_exists_on_its_group_page(self):
        """Пост с указанной группой появляется на странице этой группы."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.main_group.slug}
        ))
        first_object = response.context['page_obj'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            '15_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(str(first_object.author), self.test_user.username)
        self.assertEqual(str(first_object.group), self.main_group.title)

    def test_post_with_group_exists_on_author_profile_page(self):
        """Пост с указанной группой появляется на странице автора."""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.test_user.username}
        ))
        first_object = response.context['page_obj'][self.FIRST_OBJECT_INDEX]
        self.assertEqual(
            first_object.text,
            '15_Тестовый пост Тестовый пост Тестовый пост'
        )
        self.assertEqual(str(first_object.author), self.test_user.username)
        self.assertEqual(str(first_object.group), self.main_group.title)

    def test_post_with_group_doesnt_exist_in_another_group(self):
        """Пост с указанной группой не появляется на странице другой группы."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.empty_group.slug}
        ))
        self.assertTrue(len(response.context['page_obj']) == 0)
