import json
from datetime import timedelta
import requests
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView, UpdateView, DeleteView
from core.models import Device, File, Presentation, DeviceForm, FileForm, PlaylistForm, LocalizationForm, \
    Localization, Group, GroupForm, Slide, PlaylistEditForm, LocalizationEditForm, GroupEditForm, \
    DeviceEditForm


def index(request):
    return render(request, 'core/index.html')


def displays(request):
    display_list = Device.objects.all()
    context = {'list': display_list}
    return render(request, 'core/Displays.html', context)


def play_lists(request):
    play_lists = Presentation.objects.all()
    context = {'list': play_lists}
    return render(request, 'core/Playlists.html', context)


def files(request):
    file_list = File.objects.all()
    context = {'list': file_list}
    return render(request, 'core/Files.html', context)


class DisplayForm(FormView):
    template_name = 'core/display_form.html'
    form_class = DeviceForm
    success_url = reverse_lazy('displays')

    def form_valid(self, form):
        form.save()
        return super(DisplayForm, self).form_valid(form)


class EditDisplay(UpdateView):
    model = Device
    # form_class = DeviceEditForm
    template_name_suffix = '_edit_form'
    success_url = reverse_lazy('displays')
    fields = ['name', 'localization', 'group']

    def form_valid(self, form):
        form.save(commit=True)
        return super(EditDisplay, self).form_valid(form)


class DisplayDelete(DeleteView):
    model = Device
    success_url = reverse_lazy('displays')

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        Device.objects.filter(pk=pk).delete()
        return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


class FileUpload(FormView):
    template_name = 'core/upload_form.html'
    form_class = FileForm
    success_url = reverse_lazy('files')

    def form_valid(self, form):
        obj = form.save(commit=False)
        return super(FileUpload, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file')
        if form.is_valid():
            for f in files:
                if f.name.endswith(".mp4"):
                    obj = File.objects.create(file=f, isMP4=True)
                else:
                    if not f.name.endswith(".png"):
                        continue
                    else:
                        obj = File.objects.create(file=f, isMP4=False)
                my_file = File.objects.get(pk=obj.id)
                my_file.duration = my_file.get_duration_of_file()
                my_file.save()
                print(my_file.duration)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class FileDelete(DeleteView):
    model = File
    success_url = reverse_lazy('files')

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        File.objects.filter(pk=pk).delete()
        return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


class AddPlaylist(FormView):
    template_name = 'core/playlist_form.html'
    form_class = PlaylistForm
    success_url = reverse_lazy('playlists')

    def form_valid(self, form):
        form.save(commit=True)
        return super(AddPlaylist, self).form_valid(form)


class EditPlaylist(UpdateView):
    model = Presentation
    form_class = PlaylistEditForm
    template_name_suffix = '_edit_form'
    success_url = reverse_lazy('playlists')

    def form_valid(self, form):
        form.save(commit=True)
        return super(EditPlaylist, self).form_valid(form)


class PlaylistDelete(DeleteView):
    model = Presentation
    success_url = reverse_lazy('playlists')

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        Presentation.objects.filter(pk=pk).delete()
        return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


class ManagePlaylistSlides(TemplateView):
    template_name = 'core/manage_slides.html'
    success_url = reverse_lazy('playlists')

    def get(self, request, id):
        file_list = File.objects.all()
        slides = []
        playlist = Presentation.objects.get(pk=id)
        dbSlides = playlist.slide_set.all().order_by('order')
        for slide in dbSlides:
            durationSec = str(slide.duration).split(':', 2)[-1]
            durationMin = str(slide.duration).split(':', 2)[1]
            name = slide.slide.get_file_name()
            isMP4 = slide.slide.isMP4
            duration = slide.slide.get_duration()

            slides.append({
                "pk": slide.slide.pk,
                "slide_pk": slide.pk,
                "name": name,
                "durationSec": durationSec,
                "durationMin": durationMin,
                "duration": duration,
                "isMP4": isMP4
            })

        context = {'list': file_list,
                   'slides': slides,
                   'playlist': playlist}
        return render(request, 'core/manage_slides.html', context)

    def post(self, request, *args, **kwargs):
        playlistData = json.loads(request.body)
        playlistPK = playlistData['playlist']
        playlist = Presentation.objects.get(pk=playlistPK)
        slides = []

        for slide in playlistData['slides']:
            if not 'slide_pk' in slide:
                fileFK = File.objects.get(pk=slide['pk'])
                minutes = int(slide['durationMin'])
                seconds = int(slide['durationSec'])
                duration_time = timedelta(minutes=minutes, seconds=seconds)
                order = slide['order']
                if duration_time.total_seconds() > 1:
                    newSlide = Slide(slide=fileFK, playlist=playlist, duration=duration_time, order=order)
                    newSlide.save()
                    slides.append(newSlide)
                else:
                    return render(request, 'core/manage_slides.html', {'error': "Time for media file cannot be 0."})
            else:
                updatedSlide = playlist.slide_set.get(pk=slide['slide_pk'])
                minutes = int(slide['durationMin'])
                seconds = int(slide['durationSec'])
                duration_time = timedelta(minutes=minutes, seconds=seconds)
                order = slide['order']
                updatedSlide.duration = duration_time
                updatedSlide.order = order
                if duration_time.total_seconds() > 1:
                    updatedSlide.save()
                    slides.append(updatedSlide)
                else:
                    return render(request, 'core/manage_slides.html', {'error': "Time for media file cannot be 0."})

        fullDuration = Slide.objects.filter(playlist=playlist).aggregate(Sum('duration'))
        playlist.duration = fullDuration['duration__sum']
        playlist.save()
        return render(request, 'core/manage_slides.html')

    def delete(self, request, *args, **kwargs):
        slide = Slide.objects.get(pk=kwargs['pk'])
        slide.delete()

        return render(request, 'core/manage_slides.html')


@csrf_exempt
def register(request):
    device_id = request.POST.get('device_id')
    device_token = request.POST.get('fireBase_token')
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        device = None
    if device and device_token:
        print('register ', device_token, device_id)
        device.fireBase_token = device_token
        device.save()
        group = device.group
        if group:
            playlist = group.playlist
            print(playlist)
            if playlist:
                slide = Slide.objects.filter(playlist=playlist).order_by('order')
                if slide:
                    slides = ([{'pk': s.pk, 'order': s.order, 'name': s.slide.get_file_name(),
                                'duration': str(int(s.duration.total_seconds()))} for s in slide])
                    fireBase_token = device.fireBase_token
                    presentation = {
                        'status': '1',
                        'id': playlist.pk,
                        'start_time': str(playlist.start)[0:-9],
                        'end_time': str(playlist.end)[0:-9],
                        'slides': slides
                    }

                    url = settings.FB_URL
                    token = fireBase_token
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': settings.FB_AUTH_KEY
                    }
                    data = {'data': presentation, 'to': token}
                    r = requests.post(url, data=json.dumps(data), headers=headers)
                    print('data', json.dumps(data))
                    print('status_code', r.status_code)

    return HttpResponse(status=200)


def get_file(request, name):
    return render(request, 'core/File.html', {'name': name})


def update_devices(pk):
    groups = Group.objects.exclude(playlist=None)

    if not groups:
        return HttpResponse('Sorry, there is no devices to update. There is no groups', groups)
    else:
        for group in groups:
            playlist = group.playlist
            if not playlist:
                return HttpResponse('Sorry, there is no devices to update. There is no playlist',playlist)
            else:
                slide = Slide.objects.filter(playlist=playlist).order_by('order')
                if not slide:
                    return HttpResponse('Sorry, there is no devices to update. There is no slide', slide)
                else:
                    slides = ([{'pk': s.pk, 'order': s.order, 'name': s.slide.get_file_name(),
                                'duration': str(int(s.duration.total_seconds()))} for s in slide])
                    devices = Device.objects.filter(group=group).exclude(fireBase_token=None)
                    if not devices:
                        return HttpResponse('Sorry, there is no devices to update. There is no devices', devices)
                    else:
                        for device in devices:
                            fireBase_token = device.fireBase_token
                            presentation = {
                                'status': '1',
                                'id': playlist.pk,
                                'start_time': str(playlist.start)[0:-9],
                                'end_time': str(playlist.end)[0:-9],
                                'slides': slides
                            }

                            url = settings.FB_URL
                            token = fireBase_token
                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': settings.FB_AUTH_KEY
                            }
                            data = {'data': presentation, 'to': token}
                            r = requests.post(url, data=json.dumps(data), headers=headers)
                            print ('data', json.dumps(data))
                            print ('status_code', r.status_code)

                        return HttpResponse('Devices updated successfully!')



def localizations(request):
    localization_list = Localization.objects.all()
    devices_list = Device.objects.all()
    context = {
        'list': localization_list,
        'devices': devices_list
    }
    return render(request, 'core/Localizations.html', context)


class localizationForm(FormView):
    template_name = 'core/localization_form.html'
    form_class = LocalizationForm
    success_url = reverse_lazy('add-localization')

    def form_valid(self, form):
        form.save()
        return super(localizationForm, self).form_valid(form)


class EditLocalization(UpdateView):
    model = Localization
    form_class = LocalizationEditForm
    template_name_suffix = '_edit_form'
    success_url = reverse_lazy('localizations')

    def form_valid(self, form):
        form.save(commit=True)
        return super(EditLocalization, self).form_valid(form)


class LocalizationDelete(DeleteView):
    model = Localization
    success_url = reverse_lazy('localizations')

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        Localization.objects.filter(pk=pk).delete()
        return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


def groups(request):
    context = {
        'groups': Group.objects.all(),
        'devices': Device.objects.all(),
        'playlists': Presentation.objects.all()
    }
    return render(request, 'core/Groups.html', context)


class groupForm(FormView):
    template_name = 'core/group_form.html'
    form_class = GroupForm
    success_url = reverse_lazy('add-group')

    def form_valid(self, form):
        form.save()
        return super(groupForm, self).form_valid(form)


class EditGroup(UpdateView):
    model = Group
    form_class = GroupEditForm
    template_name_suffix = '_edit_form'
    success_url = reverse_lazy('groups')

    def form_valid(self, form):
        form.save(commit=True)
        return super(EditGroup, self).form_valid(form)


class GroupDelete(DeleteView):
    model = Group
    success_url = reverse_lazy('groups')

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        Group.objects.filter(pk=pk).delete()
        return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


class EditDeviceList(TemplateView):
    template_name = 'core/manage_groups.html'
    success_url = reverse_lazy('edit-group')

    def get(self, request, id):
        device_list_in = Device.objects.all().filter(group=id)
        device_list_not_in = Device.objects.all().exclude(group=id)
        context = {
            'device_list_in': device_list_in,
            'device_list_not_in': device_list_not_in,
            'group_id': id
        }
        return render(request, 'core/manage_groups.html', context)


@csrf_exempt
def addDeviceToGroup(request):
    group_id = request.POST.get('group_id')
    if request.POST.get('add_device_id'):
        new_list = request.POST.get('add_device_id').split(',')
        old_list = [str(e['pk']) for e in list(Device.objects.all().filter(group=group_id).values('pk'))]
        common_list = list(set(old_list).intersection(new_list))
        list_to_add = list(set(new_list) - set(common_list))
        list_to_remove = list(set(old_list) - set(common_list))
        if list_to_add:
            for id in list_to_add:
                device = Device.objects.get(pk=id)
                group = Group.objects.get(pk=group_id)
                device.group = group
                device.save()
        if list_to_remove:
            for id in list_to_remove:
                device = Device.objects.get(pk=id)
                device.group = None
                device.save()
    else:
        old_list = [str(e['pk']) for e in list(Device.objects.all().filter(group=group_id).values('pk'))]
        if old_list:
            for id in old_list:
                device = Device.objects.get(pk=id)
                device.group = None
                device.save()

    return HttpResponse(200)