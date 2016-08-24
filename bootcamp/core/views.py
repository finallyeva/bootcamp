import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from bootcamp.feeds.models import Feed
from bootcamp.feeds.views import feeds, FEEDS_NUM_PAGES

from .forms import ProfileForm, ChangePasswordForm, SavePictureForm


def home(request):
    return feeds(request)


def network(request):
    users = User.objects.filter(is_active=True).order_by('username')
    return render(request, 'core/network.html', {'users': users})


def profile(request, username):
    page_user = get_object_or_404(User, username=username)
    all_feeds = Feed.get_feeds().filter(user=page_user)
    paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
    feeds = paginator.page(1)

    from_feed = -1

    if feeds:
        from_feed = feeds[0].id

    context = {
        'page_user': page_user, 'feeds': feeds,
        'from_feed': from_feed, 'page': 1
    }
    return render(request, 'core/profile.html', context)


@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.profile.job_title = form.cleaned_data.get('job_title')
            user.email = form.cleaned_data.get('email')
            user.profile.url = form.cleaned_data.get('url')
            user.profile.location = form.cleaned_data.get('location')
            user.save()

            message = _('Your profile were successfully edited.')
            messages.add_message(request, messages.SUCCESS, message)
    else:
        initial = {
            'job_title': user.profile.job_title,
            'url': user.profile.url,
            'location': user.profile.location
        }
        form = ProfileForm(instance=user, initial=initial)

    return render(request, 'core/settings.html', {'form': form})


@login_required
def picture(request):
    uploaded_picture = False
    picture_url = None

    user = request.user

    if request.GET.get('upload_picture') == 'uploaded':
        uploaded_picture = True
        source = '{0}.jpg'.format(user.username)

        picture_url, _ = cloudinary_url(source, secure=True)

    context = {
        'uploaded_picture': uploaded_picture,
        'picture_url': picture_url,
    }
    return render(request, 'core/picture.html', context)


@login_required
def password(request):
    user = request.user

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)

        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            user.set_password(new_password)
            user.save()

            message = _('Your password were successfully changed.')
            messages.add_message(request, messages.SUCCESS, message)
    else:
        form = ChangePasswordForm(instance=user)

    return render(request, 'core/password.html', {'form': form})


@login_required
def upload_picture(request):
    user = request.user
    picture_id = '{0}'.format(user.username)

    cloudinary.uploader.upload(
        request.FILES['picture'],
        public_id=picture_id,
    )

    return redirect('/settings/picture/?upload_picture=uploaded')


@login_required
def save_uploaded_picture(request):
    form = SavePictureForm(request.POST)

    if form.is_valid():
        user = request.user
        source = '{0}.jpg'.format(user.username)
        crop_picture_url, _ = cloudinary_url(
            source, secure=True, crop='crop', **form.cleaned_data)

        user.profile.picture_url = crop_picture_url
        user.save()

    return redirect('/settings/picture/')
