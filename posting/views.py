from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Post, Category, Comment
from .forms import CommentForm
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify

# Create your views here.

class PostList(ListView):
    model = Post
    ordering = '-pk'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostList, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()

        return context

class PostDetail(DetailView):
    model = Post

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostDetail, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        context['comment_form']=CommentForm
        return context



class PostCreate(LoginRequiredMixin,CreateView):
    model = Post
    fields = ['title', 'content', 'reliability', 'head_image', 'category']

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated and (current_user.is_staff or current_user.is_superuser):
            form.instance.author = current_user
            response = super(PostCreate, self).form_valid(form)

            return response
        else:
            return redirect('/posting/')

class PostUpdate(LoginRequiredMixin, UpdateView): # 모델명_form
    model = Post
    fields = ['title', 'content', 'reliability', 'head_image', 'category']

    template_name = 'posting/post_update_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author :
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else :
            raise PermissionDenied

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostUpdate, self).get_context_data()
        return context

    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)

        return response
class CommentUpdate(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user ==self.get_object().author:
            return super(CommentUpdate, self).dispatch(request,*args, **kwargs)
        else:
            raise PermissionDenied

def category_page(request, slug):
    if slug == 'no_category':
        category = '미분류'
        post_list = Post.objects.filter(category=None)
    else :
        category = Category.objects.get(slug=slug)
        post_list = Post.objects.filter(category=category)

    return render(request, 'posting/post_list.html',
                  {
                      'post_list' : post_list,
                      'categories' : Category.objects.all(),
                      'no_category_post_count' : Post.objects.filter(category=None).count(),
                      'category' : category
                  })
def new_comment(request, pk):
    if request.user.is_authenticated:
        post=get_object_or_404(Post,pk=pk)

        if request.method=="POST":
            comment_form=CommentForm(request.POST)
            if comment_form.is_valid():
                comment=comment_form.save(commit=False)
                comment.post=post
                comment.author=request.user
                comment.save()
                return redirect(comment.get_absolute_url())
            else:
                return redirect(post.get_absolute_url())
        else:
            raise PermissionDenied

def delete_comment(request, pk):
    comment=get_object_or_404(Comment,pk=pk)
    post=comment.post

    if request.user.is_authenticated and request.user == comment.author:
        comment.delete()
        return redirect(post.get_absolute_url())
    else:
        raise PermissionDenied

