from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Post
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count



def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    # Pagingator with 3 posts per page
    paginator = Paginator(post_list, 3)
    tag = None
    if tag_slug:
        tag=get_object_or_404(Tag,slug = tag_slug)
        post_list = post_list.filter(tags__in=[tag])
        
    page_number = request.GET.get('page',1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer get the first page
        posts = paginator.page(1)    
    except EmptyPage:
        # If page_number is out of range get last page of results
        posts = paginator.page(paginator.num_pages)
    
    context={
        'posts':posts,
        'tag':tag
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day)
    comments = post.comments.filter(active=True)
    
    form = CommentForm()
    post_tags_ids =post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by ('-same_tags','publish')[:4]
    context={
        'post':post,
        'comments':comments,
        'form':form,
        'similar_posts':similar_posts
        
    }
    return render(
        request,
        'blog/post_detail.html',
        context
        
    )

def post_share(request, post_id):
    # Retrieve post by id. 
    post=get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    
    sent=False
    if request.method == 'POST':
        form=EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url=request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = (f"{cd['name']} ({cd['email']}) " 
                      f"recommends you read {post.title}"
            )        
            message = (
                f"Read {'post.title'} at {post_url}\n\n" 
                f"{cd['name']}\'s comments:{cd['comments']}"
            )    
                
            send_mail(subject=subject,
                      message=message,
                      from_email='cromarties2913@gmailcom',
                      recipient_list=[cd['to']]
            )
            sent = True    
    else:
        form = EmailPostForm()
            
    context={
        'post':post,
        'form':form,
        'sent':sent
    }    
    return render(request,'blog/share.html', context)

 