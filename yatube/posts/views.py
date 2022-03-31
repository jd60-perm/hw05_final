from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

LIST_VOLUME: int = 10
CACHE_DELAY_SECONDS: float = 20

@cache_page(CACHE_DELAY_SECONDS)
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.order_by('-pub_date')
    paginator = Paginator(post_list, LIST_VOLUME)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by('-pub_date')
    paginator = Paginator(post_list, LIST_VOLUME)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    selected_user = get_object_or_404(User, username=username)
    post_list = selected_user.posts.order_by('-pub_date')
    count = selected_user.posts.count
    paginator = Paginator(post_list, LIST_VOLUME)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/profile.html'
    following = request.user.is_authenticated and Follow.objects.filter(
            user=request.user,
            author=selected_user
        ).exists()
    context = {
        'author': selected_user,
        'count': count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    selected_post = get_object_or_404(Post, pk=post_id)
    count = selected_post.author.posts.count
    comments = selected_post.comments.all()
    context = {
        'selected_post': selected_post,
        'count': count,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {'form': form, 'is_edit': False}
    return render(request, 'posts/create_post.html', context)


def post_edit(request, post_id):
    selected_post = get_object_or_404(Post, pk=post_id)
    if selected_post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=selected_post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': True, 'post_id': post_id}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).order_by('-pub_date')
    paginator = Paginator(post_list, LIST_VOLUME)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not Follow.objects.filter(
            user=request.user,
            author__exact=author
        ).exists():
            Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
