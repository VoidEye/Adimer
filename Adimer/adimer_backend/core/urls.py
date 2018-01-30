from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^$', views.displays, name='index'),

    url(r'^playlists/$', views.play_lists, name='playlists'),
    url(r'^files/$', views.files, name='files'),
    url(r'^upload/$', views.FileUpload.as_view(), name='upload'),

    url(r'^displays/$', views.displays, name='displays'),
    url(r'^add-display/$', views.DisplayForm.as_view(), name='add-display'),
    url(r'^edit-display/(?P<pk>\d+)', views.EditDisplay.as_view(), name='edit-display'),
    url(r'^delete-display/(?P<pk>\d+)', views.DisplayDelete.as_view(), name='delete-display'),

    url(r'^delete-file/(?P<pk>\d+)', views.FileDelete.as_view(), name='delete-file'),

    url(r'^add-playlist/$', views.AddPlaylist.as_view(), name='add-playlist'),
    url(r'^update-devices/$', views.update_devices),
    url(r'^manage-slides/(?P<id>\w+)/$', views.ManagePlaylistSlides.as_view(), name='manage-slides'),
    url(r'^manage-slides/(?P<id>\w+)/(?P<pk>\w+)/$', views.ManagePlaylistSlides.as_view(), name='manage-slides'),
    url(r'^edit-playlist/(?P<pk>\d+)/$', views.EditPlaylist.as_view(), name='edit-playlist'),
    url(r'^delete-playlist/(?P<pk>\d+)', views.PlaylistDelete.as_view(), name='delete-playlist'),

    url(r'^register/$', views.register),

    url(r'^add-localization/$', views.localizationForm.as_view(), name='add-localization'),
    url(r'^localizations/$', views.localizations, name='localizations'),
    url(r'^edit-localization/(?P<pk>\d+)/$', views.EditLocalization.as_view(), name='edit-localization'),
    url(r'^delete-localization/(?P<pk>\d+)', views.LocalizationDelete.as_view(), name='delete-localization'),

    url(r'^groups/$', views.groups, name='groups'),
    url(r'^add-group/$', views.groupForm.as_view(), name='add-group'),
    url(r'^manage-group/(?P<id>\w+)', views.EditDeviceList.as_view(), name='manage-group'),
    url(r'^delete-group/(?P<pk>\w+)', views.GroupDelete.as_view(), name='delete-group'),
    url(r'^edit-group/(?P<pk>\w+)', views.EditGroup.as_view(), name='edit-group'),

    # url(r'^add-playlist-to-group/(?P<pk>\w+)/$', views.AddPlaylistToGroup.as_view(), name='add-playlist-to-group'),
    url(r'add-device-to-group/$', views.addDeviceToGroup),

]
