from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import *
from .models import *
from blog.models import *
from PIL import Image
from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q
# Create your views here.
def register(request):

    if(request.method == 'POST'):
        form = UserRegisterForm(request.POST)
        if(form.is_valid()):
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Your Account Has Been Created. Sign In To Get Started, {username}!")
            try:
                new_user = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=new_user)
                new_settings = ProfileSettings.objects.create(user=new_user)
                print(f"{request.user.username} account has been created.")
            except:
                pass
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form':form, 'title':'Register','hide_post' : True, 'show_bottom_detail' : True})

@login_required
def profile(request):
    if (request.method == 'POST'):
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        profile_form = ProfileNickUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        profileSettings_form = ProfileSettingsUpdateForm(request.POST, request.FILES, instance=request.user.profilesettings)

        if (u_form.is_valid() and p_form.is_valid() and profile_form.is_valid() and profileSettings_form.is_valid()):
            u_form.save()
            p_form.save()
            profile_form.save()
            cover = profileSettings_form.cleaned_data.get('coverImage')
            profileSettings_form.save()
            ps = request.user.profilesettings
            ps = ProfileSettings(user=ps.user,about=ps.about, quote=ps.quote, coverImage=cover, id=ps.id)
            ps.save()
            messages.success(request, f"Your Account Has Been Updated!")
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        profile_form = ProfileNickUpdateForm(instance=request.user.profile)
        profileSettings_form = ProfileSettingsUpdateForm(instance=request.user.profilesettings)

    context = {
    'u_form' : u_form,
    'p_form' : p_form,
    'profile_form' : profile_form,
    'profileSettings_form' : profileSettings_form,
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

    return render(request, 'users/profile.html', context)

@login_required
def group(request, name=None):

    group = Group.objects.get(name=name)
    groupSettings = GroupSettings.objects.get(group=group)

    def isOwner():
        try:
            return (request.user == group.owner)
        except:
            return False

    def isMod():
        try:
            return (request.user in group.mods.all())
        except:
            return False

    if (request.method == 'POST'):
        group_form = GroupUpdateForm(request.POST, request.FILES, instance=group)
        groupSettings_form = GroupSettingsUpdateForm(request.POST, request.FILES, instance=groupSettings)

        if (group_form.is_valid() and groupSettings_form.is_valid()):

            new_name = group_form.cleaned_data.get('name')
            new_image = group_form.cleaned_data.get('image')
            new_members = group_form.cleaned_data.get('members')
            new_private = group_form.cleaned_data.get('private')
            group_form.save()
            new_cover = groupSettings_form.cleaned_data.get('coverImage')
            new_quote = groupSettings_form.cleaned_data.get('quote')
            new_about = groupSettings_form.cleaned_data.get('about')
            groupSettings_form.save()

            new_group = Group(name=new_name,image=new_image,private=new_private, id=group.id, owner=group.owner)
            new_group.members.set(new_members)
            new_groupSettings = GroupSettings(coverImage=new_cover,quote=new_quote,about=new_about, group=group, id=groupSettings.id)

            for person in new_group.members.all():
                new_notification = Notification(sender=request.user, recepient=person, type=5, group=new_group)
                if(new_notification.sender != new_notification.recepient):
                    new_notification.save()

            new_group.save()
            new_groupSettings.save()

            messages.success(request, f"Your Group Settings Have Been Updated!")
            return redirect('group',group.name)

    else:
        group_form = GroupUpdateForm(instance=group)
        groupSettings_form = GroupSettingsUpdateForm(instance=groupSettings)
        group_form.fields["members"].queryset = User.objects.filter(Q(members=group) | Q(profile__friends=request.user.profile)).order_by("username").distinct()
        #group_form.fields["mods"].queryset = User.objects.filter(Q(mods=group) | Q(members=group)).order_by("username")

    context = {
    'group_form' : group_form,
    'groupSettings_form' : groupSettings_form,
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True,
    'group' : group,
    'groupSettings' : groupSettings,
    'is_moderator' : isMod(),
    'is_owner' : isOwner(),
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

    return render(request, 'users/group.html', context)

def group_new(request):

    group = Group(name="New Group", owner=request.user)
    groupSettings = GroupSettings(group=group)

    if (request.method == 'POST'):
        group_form = GroupUpdateForm(request.POST, request.FILES, instance=group)
        groupSettings_form = GroupSettingsUpdateForm(request.POST, request.FILES, instance=groupSettings)

        if (group_form.is_valid() and groupSettings_form.is_valid()):

            new_name = group_form.cleaned_data.get('name')
            new_image = group_form.cleaned_data.get('image')
            new_members = group_form.cleaned_data.get('members')
            new_private = group_form.cleaned_data.get('private')

            new_cover = groupSettings_form.cleaned_data.get('coverImage')
            new_quote = groupSettings_form.cleaned_data.get('quote')
            new_about = groupSettings_form.cleaned_data.get('about')

            new_group = Group.objects.create(name=new_name,image=new_image,private=new_private, owner=request.user)
            new_group.members.set(new_members)
            new_groupSettings = GroupSettings.objects.create(coverImage=new_cover,quote=new_quote,about=new_about, group=new_group)

            new_group.save()
            new_groupSettings.save()

            return redirect('group-posts',group.name)

    else:
        group_form = GroupUpdateForm(instance=group)
        groupSettings_form = GroupSettingsUpdateForm(instance=groupSettings)
        group_form.fields["members"].queryset = User.objects.filter(Q(profile__friends=request.user.profile)).order_by("username")
        #group_form.fields["mods"].queryset = User.objects.filter(Q(mods=group) | Q(members=group)).order_by("username")

    context = {
    'group_form' : group_form,
    'groupSettings_form' : groupSettings_form,
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True,
    'group' : group,
    'groupSettings' : groupSettings,
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

    return render(request, 'users/new_group.html', context)

@login_required
def group_manager(request):

    groups = Group.objects.filter(Q(owner=request.user) | Q(members=request.user) | Q(mods=request.user) ).distinct()


    context = {
    'groups': groups,
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True,
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Delete_Group"):
            group_obj = Group.objects.get(id=request.POST.get('id'))
            group_obj.delete()
            messages.success(request, f"Group Deleted Successfully")
            return redirect('group_manager')

    return render(request, 'users/groups_manager.html', context)

@login_required
def feedback(request):
    if (request.method == 'POST'):
        form = FeedbackForm(request.POST, instance=request.user)
        if (form.is_valid()):
            form.save()

            op1 = form.cleaned_data.get('quality_speed')
            op2 = form.cleaned_data.get('quality_features')
            op3 = form.cleaned_data.get('quality_visual')
            op4 = form.cleaned_data.get('quality_stability')
            op5 = form.cleaned_data.get('quality_responsiveness')
            op6 = form.cleaned_data.get('comment')

            feedback = Feedback(quality_speed=op1,quality_features=op2,quality_visual=op3,quality_stability=op4
            ,quality_responsiveness=op5,comment=op6, author=request.user)
            feedback.save()

            messages.success(request, f"Your feedback has been sent.")
            return redirect('feedback-sent')

    else:
        form = FeedbackForm(instance=request.user)

    context = {
    'form' : form,
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return render(request, 'users/feedback.html', context)

    return render(request, 'users/feedback.html', context)

@login_required
def feedback_sent(request):

    context = {
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return render(request, 'users/feedback.html', context)

    return render(request, 'users/feedback_sent.html', context)

def about(request):

    context = {

    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return render(request, 'users/feedback.html', context)

    return render(request, 'users/about.html', context)

@login_required
def privacy(request):

    context = {
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return render(request, 'users/feedback.html', context)

    return render(request, 'users/privacy.html', context)

def terms_of_service(request):

    context = {
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return render(request, 'users/feedback.html', context)

    return render(request, 'users/terms_of_service.html', context)

@login_required
def legal(request):

    context = {
    'notifications' : Notification.objects.filter(recepient=request.user).order_by('-date_posted'),
    'requests' : Request.objects.filter(recepient=request.user).order_by('-date_posted'),
    'badge_count' : Request.objects.filter(recepient=request.user, confirmed=False).count() +
    Notification.objects.filter(recepient=request.user, confirmed=False).count(),
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    if request.is_ajax():
        if (request.POST.get('action') == "Open_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Notifications"):
            notifications = Notification.objects.filter(recepient=request.user)
            notifications.delete()
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Open_Requests"):
            requests = Request.objects.filter(recepient=request.user, confirmed=False).update(confirmed=True)
            html = render_to_string('blog/notifications_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Clear_Requests"):
            requets = Request.objects.filter(recepient=request.user)
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Decline_Request"):
            requets = Request.objects.get(id=request.POST.get('request_id'))
            requets.delete()
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return JsonResponse({'form':html})

        elif (request.POST.get('action') == "Accept_Request"):
            request_obj = Request.objects.get(id=request.POST.get('request_id'))
            request.user.profile.friends.add(request_obj.sender.profile)
            html = render_to_string('blog/requests_view.html', context, request=request)
            return render(request, 'users/feedback.html', context)

    return render(request, 'users/legal.html', context)

def welcome(request):

    context = {
    'hide_post' : True,
    'show_bottom_detail' : True
    }

    return render(request, 'users/welcome.html', context)
