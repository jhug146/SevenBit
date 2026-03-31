from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from ui.website import views

urlpatterns = [
    path("",                            views.items,              name="items"),
    path("import/",                     views.import_csv,         name="import_csv"),
    path("item/<int:n>/",               views.item_detail,        name="item_detail"),
    path("item/<int:n>/save/",          views.save_item,          name="save_item"),
    path("item/<int:n>/upload/",        views.upload_item,        name="upload_item"),
    path("upload/",                     views.upload_display,     name="upload_display"),
    path("upload/start/",               views.start_upload,       name="start_upload"),
    path("upload/stop/",                views.stop_upload,        name="stop_upload"),
    path("upload/stream/",              views.upload_stream,      name="upload_stream"),
    path("switch-account/",             views.switch_account,     name="switch_account"),
    path("switch-item-type/",           views.switch_item_type,   name="switch_item_type"),
    path("upload-mode/",                views.update_upload_mode, name="update_upload_mode"),
    path("download/",                   views.download_items,     name="download_items"),
    path("status/",                     views.get_status,         name="get_status"),
    path("img/<path:image_path>",       views.serve_image,        name="serve_image"),
]

urlpatterns += staticfiles_urlpatterns()
