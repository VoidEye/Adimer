import json
import os
from datetime import timedelta
import imageio
import magic
import requests
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.forms import ModelForm
from django.urls import reverse_lazy
from firebase import firebase
from datetime import timedelta
import math
imageio.plugins.ffmpeg.download()
from moviepy.editor import VideoFileClip

allowed_file_types = ['PNG', 'MP4', 'MPEG v4', 'MPEG-4']


class Localization(models.Model):
    name = models.CharField(max_length=100)
    shop_name = models.CharField(max_length=100)
    city = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class LocalizationForm(ModelForm):
    class Meta:
        model = Localization
        fields = ['name', 'shop_name', 'city']

    def __init__(self, *args, **kwargs):
        super(LocalizationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('add-localization')  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field1 will appear first in HTML
            'shop_name',  # field2 will appear second in HTML
            'city',
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )


class LocalizationEditForm(ModelForm):
    class Meta:
        model = Localization
        fields = ['name', 'shop_name', 'city']

    def __init__(self, *args, **kwargs):
        super(LocalizationEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('edit-localization', args=[self.instance.id])  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field1 will appear first in HTML
            'shop_name',  # field2 will appear second in HTML
            'city',
            Submit('submit', u'Submit', css_class='btn btn-success'),
            Submit('cancel', 'Cancel', css_class='btn-default'),
        )


class File(models.Model):
    file = models.FileField(upload_to='slides', null=False)
    isMP4 = models.BooleanField()
    duration = models.FloatField(null=True)

    def __str__(self):
        return self.file.name.split('/', 1)[-1]

    def get_file_name(self):
        return self.file.name.split('/', 1)[-1]

    def get_duration_of_file(self):
        if self.isMP4:
            print("HERE")
            clip = VideoFileClip("/app/adimer_backend/" + self.file.url)
            duration_float = math.ceil(clip.duration)
            del clip
            return duration_float

    def get_duration(self):
        if self.isMP4:
            print(self.duration)
            minutes = int(math.floor(self.duration / 60))
            seconds = int(self.duration - minutes * 60)
            return {"minutes": minutes,
                    "seconds": seconds}


@receiver(pre_delete, sender=File)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(pre_save, sender=File)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = File.objects.get(pk=instance.pk).file
    except File.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


class FileForm(ModelForm):

    def clean_file(self):
        uploadedFile = self.cleaned_data.get("file", False)
        filetype = magic.from_buffer(uploadedFile.read())

        if any(el in filetype for el in allowed_file_types):
            return uploadedFile
        raise ValidationError("File is not in the valid format (PNG or MP4).")

    class Meta:
        model = File
        fields = ["file"]

    def __init__(self, *args, **kwargs):
        super(FileForm, self).__init__(*args, **kwargs)
        file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
        self.fields['file'] = file_field
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('upload')  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'file',
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )


class Group(models.Model):
    name = models.CharField(max_length=150, unique=True)
    playlist = models.ForeignKey('Presentation', null=True, default=None, on_delete=models.SET_NULL, related_name='+')
    def __str__(self):
        return self.name

@receiver(pre_save, sender=Group)
def sendMessageToDevicesInGroup99(sender, instance, **kwargs):

    if not instance.pk:
        return False

    try:
        group = Group.objects.get(pk=instance.pk)
    except Presentation.DoesNotExist:
        return False

    try:
        old_playlist = Group.objects.get(pk=instance.pk).playlist
    except Presentation.DoesNotExist:
        return False

    new_playlist = instance.playlist

    if not old_playlist == new_playlist:
        devices = Device.objects.filter(group=group).exclude(fireBase_token=None)
        if devices:
            for device in devices:
                fireBase_token = device.fireBase_token
                presentation = {
                    'status': settings.STATUS_DELETE_PLAYLIST,
                    'playlist': old_playlist.pk
                }

                url = settings.FB_URL
                token = fireBase_token
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': settings.FB_AUTH_KEY
                }
                data = {'data': presentation, 'to': token}

                r = requests.post(url, data=json.dumps(data), headers=headers)
                print(json.dumps(data))
                print(r.status_code)

            for device in devices:
                slide = Slide.objects.filter(playlist=new_playlist).order_by('order')
                if slide:
                    slides = ([{'pk': s.pk, 'order': s.order, 'name': s.slide.get_file_name(),
                                'duration': str(int(s.duration.total_seconds()))} for s in slide])
                    fireBase_token = device.fireBase_token
                    presentation = {
                        'status': '0',
                        'id': new_playlist.pk,
                        'start_time': str(new_playlist.start)[0:-9],
                        'end_time': str(new_playlist.end)[0:-9],
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

					
@receiver(pre_delete, sender=Group)
def sendMessageToDevicesInGroup(sender, instance, **kwargs):
    group = Group.objects.get(pk=instance.pk)
    if group:
        devices = Device.objects.filter(group=group).exclude(fireBase_token=None)
        if devices:
            for device in devices:

                fireBase_token = device.fireBase_token
                presentation = {
                    'status': settings.STATUS_DELETE_GROUP,
                }

                url = settings.FB_URL
                token = fireBase_token
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': settings.FB_AUTH_KEY
                }
                data = {'data': presentation, 'to': token}

                r = requests.post(url, data=json.dumps(data), headers=headers)
                print (json.dumps(data))
                print (r.status_code)


class Presentation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slides = models.ManyToManyField(File, through='Slide', null=True)
    duration = models.DurationField(default=timedelta(seconds=0))
    start = models.DateTimeField()
    end = models.DateTimeField()
    group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL, default=None)

    def __str__(self):
        return self.name

		
class PlaylistEditForm(ModelForm):
    class Meta:
        model = Presentation
        fields = ['start', 'end']

    def __init__(self, *args, **kwargs):
        super(PlaylistEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('edit-playlist', args=[self.instance.id])  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'start',
            'end',
            Submit('submit', u'Submit', css_class='btn btn-success'),
            Submit('cancel', 'Cancel', css_class='btn-default'),
        )


class PlaylistForm(ModelForm):
    class Meta:
        model = Presentation
        fields = ['name', 'start', 'end']
        labels = {
            'start': "Start <i style=\"font-size:x-small\">YYYY-MM-DD HH:MM</i>",
            'end': "End <i style=\"font-size:x-small\">YYYY-MM-DD HH:MM</i>",
        }

    def __init__(self, *args, **kwargs):
        super(PlaylistForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('add-playlist')  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field2 will appear second in HTML
            'start',
            'end',
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )

@receiver(pre_delete, sender=Presentation)
def sendMessageToDevicesInGroup(sender, instance, **kwargs):
    groups = Group.objects.filter(playlist=instance.pk)
    if groups:
        for group in groups:
            devices = Device.objects.filter(group=group).exclude(fireBase_token=None)
            if devices:
                for device in devices:

                    fireBase_token = device.fireBase_token
                    presentation = {
                        'status': settings.STATUS_DELETE_PLAYLIST,
                        'playlist': instance.pk
                    }

                    url = settings.FB_URL
                    token = fireBase_token
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': settings.FB_AUTH_KEY
                    }
                    data = {'data': presentation, 'to': token}

                    r = requests.post(url, data=json.dumps(data), headers=headers)
                    print (json.dumps(data))
                    print (r.status_code)


class Slide(models.Model):
    # pk = models.IntegerField(unique=True, null=False)
    slide = models.ForeignKey(File)
    playlist = models.ForeignKey(Presentation)
    duration = models.DurationField(null=True) #!! develop mode
    order = models.IntegerField(null=False)

    def __str__(self):
        return "id:" + str(self.pk) + ",name:" + self.slide.get_file_name() + ", duration: " + str(self.duration) + ", order: " + str(self.order)


class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('add-group')  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field2 will appear second in HTML
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )


class GroupEditForm(ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'playlist']

    def __init__(self, *args, **kwargs):
        super(GroupEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('edit-group', args=[self.instance.id])  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field2 will appear second in HTML
            'playlist',
            Submit('submit', u'Submit', css_class='btn btn-success'),
            Submit('cancel', 'Cancel', css_class='btn-default'),
        )


class AddPlaylistForm(ModelForm):
    class Meta:
        model = Group
        fields = ['playlist']

    def __init__(self, *args, **kwargs):
        super(AddPlaylistForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('add-playlist-to-group', args=[self.instance.id])  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'playlist',  # field2 will appear second in HTML
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )


class Device(models.Model):
    ip = models.GenericIPAddressField()
    name = models.CharField(max_length=50, unique=True)
    localization = models.ForeignKey(Localization, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=False)
    last_connection = models.DateTimeField(null=True)
    device_id = models.CharField(max_length=255, null=True, unique=True)
    fireBase_token = models.CharField(max_length=255, null=True)
    group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL)


@receiver(pre_save, sender=Device)
def check_limits(sender, **kwargs):

    instance = kwargs['instance'].pk
    if instance is None:
        fb = firebase.FirebaseApplication(settings.FB, None)
        limit = fb.get('/limit', None)
        devices = sender.objects.count()
        if devices + 1 > limit:
            raise PermissionDenied


@receiver(pre_delete, sender=Device)
def sendMessageToDevice(sender, instance, **kwargs):
    device = Device.objects.get(pk=instance.pk)
    if device.fireBase_token is not None:
        fireBase_token = device.fireBase_token
        presentation = {
            'status': settings.STATUS_DELETE_DEVICE,
        }

        url = settings.FB_URL
        token = fireBase_token
        headers = {
            'Content-Type': 'application/json',
            'Authorization': settings.FB_AUTH_KEY
        }
        data = {'data': presentation, 'to': token}

        r = requests.post(url, data=json.dumps(data), headers=headers)
        print (json.dumps(data))
        print (r.status_code)


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        fields = ['name', 'ip', 'localization', 'device_id', 'group']

    def __init__(self, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('add-display')  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field1 will appear first in HTML
            'ip',  # field2 will appear second in HTML
            'localization',
            'device_id',
            'group',
            Submit('submit', u'Submit', css_class='btn btn-success'),
        )


class DeviceEditForm(ModelForm):
    class Meta:
        model = Device
        fields = ['name', 'ip', 'localization', 'device_id', 'group']

    def __init__(self, *args, **kwargs):
        super(DeviceEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'  # this line sets your form's method to post
        self.helper.form_action = reverse_lazy('edit-display', args=[self.instance.id])  # this line sets the form action
        self.helper.layout = Layout(  # the order of the items in this layout is important
            'name',  # field1 will appear first in HTML
            'ip',  # field2 will appear second in HTML
            'localization',
            'device_id',
            'group',
            Submit('submit', u'Submit', css_class='btn btn-success'),
            Submit('cancel', 'Cancel', css_class='btn-default'),
        )


class Connection(models.Model):
    device = models.ForeignKey(Device)
    time = models.DateTimeField()
    status = models.SmallIntegerField()