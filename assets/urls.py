from django.urls import path
from .views import (
    AssetListView, AssetCreateView, AssetEditView, 
    AssetMoveView, AssetHistoryView, AssetDeleteView,
    asset_ku_view, asset_bulk_delete, asset_delete_all,
    asset_export_excel, asset_export_pdf, asset_import_excel,   # 🔥 ini ditambahkan
)
from . import views

urlpatterns = [
    path('', AssetListView.as_view(), name='asset_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', AssetCreateView.as_view(), name='asset_create'),
    path('edit/<str:asset_id>/', AssetEditView.as_view(), name='asset_edit'),
    path('move/<str:asset_id>/', AssetMoveView.as_view(), name='asset_move'),
    path('history/<str:asset_id>/', AssetHistoryView.as_view(), name='asset_history'),
    path('delete/<str:asset_id>/', AssetDeleteView.as_view(), name='asset_delete'),
    path('asset-ku/', asset_ku_view, name='asset_ku'),
    path('assets/bulk-delete/', asset_bulk_delete, name='asset_bulk_delete'),
    path('assets/delete-all/', asset_delete_all, name='asset_delete_all'),

    # 🔥 Tambahan baru untuk Export / Import fitur
    path('assets/export/excel/', asset_export_excel, name='asset_export_excel'),
    path('assets/export/pdf/', asset_export_pdf, name='asset_export_pdf'),
    path('assets/import/excel/', asset_import_excel, name='asset_import_excel'),
]
