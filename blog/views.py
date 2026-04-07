from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm

def index(request):
    """Главная страница с пагинацией - только опубликованные посты"""
    posts = Post.published_objects.published().annotate(
        comment_count=Count('comments')
    ).select_related('category', 'location', 'author')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)

def post_detail(request, post_id):
    """Страница отдельной публикации"""
    post = get_object_or_404(Post, id=post_id)
    
    if not post.is_published and request.user != post.author:
        raise Http404("Пост не найден")
    
    if not post.category.is_published and request.user != post.author:
        raise Http404("Пост не найден")
    
    if post.pub_date > timezone.now() and request.user != post.author:
        raise Http404("Пост не найден")
    
    if request.user != post.author:
        post = get_object_or_404(
            Post.objects.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            ),
            id=post_id
        )
    
    comments = post.comments.all()
    form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)

def category_posts(request, category_slug):
    """Страница категории с пагинацией - только опубликованные посты"""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = Post.published_objects.published().filter(
        category=category
    ).annotate(
        comment_count=Count('comments')
    ).select_related('category', 'location', 'author')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)

def profile(request, username):
    """Страница пользователя с пагинацией - автор видит все свои посты"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    author = get_object_or_404(User, username=username)

    if request.user == author:
        posts = Post.objects.filter(author=author).select_related(
            'category', 'location'
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    else:
        posts = Post.published_objects.published().filter(
            author=author
        ).annotate(
            comment_count=Count('comments')
        ).select_related('category', 'location')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': author,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)

@login_required
def post_create(request):
    """Создание нового поста"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})

@login_required
def post_edit(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form, 'post': post})

@login_required
def post_delete(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/delete.html', {'post': post})

@login_required
@require_http_methods(['POST'])
def add_comment(request, post_id):
    """Добавление комментария"""
    post = get_object_or_404(
        Post,
        id=post_id,
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('blog:post_detail', post_id=post_id)

@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})

@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/delete_comment.html', {'comment': comment})
