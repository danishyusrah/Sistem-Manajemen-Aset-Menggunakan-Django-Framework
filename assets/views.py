import requests
import io
import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.views.decorators.csrf import csrf_exempt

# Pakai session login_required custom
from .utils.decorators import session_login_required  # pastikan path sesuai

# Supabase Configuration
SUPABASE_URL = 'https://mdgcgvvghvjofjtbpxcb.supabase.co'
SUPABASE_API_KEY = 'YOUR-API-KEY'

HEADERS = {
    'apikey': SUPABASE_API_KEY,
    'Authorization': f'Bearer {SUPABASE_API_KEY}',
    'Content-Type': 'application/json'
}

# 🔥 Bulk Delete Aset
@session_login_required
def asset_bulk_delete(request):
    user = request.session.get('user')

    if request.method == 'POST':
        if user.get('role') == 'admin':
            ids = request.POST.getlist('selected_assets')
            if ids:
                for asset_id in ids:
                    res = requests.delete(f'{SUPABASE_URL}/rest/v1/assets?id=eq.{asset_id}', headers=HEADERS)
                    if res.status_code != 204:
                        messages.error(request, f"Gagal menghapus aset ID {asset_id}.")
                        break
                else:
                    messages.success(request, f"{len(ids)} aset berhasil dihapus.")
            else:
                messages.warning(request, "Tidak ada aset yang dipilih.")
        else:
            messages.error(request, "Anda tidak punya izin untuk menghapus aset.")
    return redirect('asset_list')

# 🔥 Delete Semua Aset
@session_login_required
def asset_delete_all(request):
    user = request.session.get('user')

    if user.get('role') == 'admin':
        Asset.objects.all().delete()
        messages.success(request, "Semua aset berhasil dihapus.")
    else:
        messages.error(request, "Anda tidak memiliki izin untuk melakukan ini.")
    return redirect('asset_list')

# 🔥 View Aset Milik User
@session_login_required
def asset_ku_view(request):
    user = request.session.get('user')

    if user['role'] != 'user':
        return redirect('dashboard')

    search_query = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    per_page = 10

    url = f'{SUPABASE_URL}/rest/v1/assets?select=*'

    if search_query:
        url += f"&name=ilike.*{search_query}*"

    res = requests.get(url, headers=HEADERS)

    assets = res.json() if res.status_code == 200 else []

    total_assets = len(assets)
    start = (page - 1) * per_page
    end = start + per_page
    assets_paginated = assets[start:end]

    total_pages = (total_assets + per_page - 1) // per_page

    return render(request, 'assets/asset_ku.html', {
        'assets': assets_paginated,
        'user': user,
        'search_query': search_query,
        'page': page,
        'total_pages': total_pages,
    })

# 🔥 Dashboard User
@session_login_required
def dashboard_user(request):
    user = request.session.get('user')
    return render(request, 'dashboard_user.html', {'user': user})

# 🔥 Dashboard Admin
@session_login_required
def dashboard(request):
    user = request.session.get('user')
    return render(request, 'dashboard.html', {'user': user})

# 🔥 List Semua Aset
class AssetListView(View):
    def get(self, request):
        user = request.session.get('user')

        search_query = request.GET.get('search', '')
        category = request.GET.get('category', '')
        location = request.GET.get('location', '')

        url = f'{SUPABASE_URL}/rest/v1/assets'
        filters = []

        if search_query:
            filters.append(f"name=ilike.*{search_query}*")
        if category:
            filters.append(f"category=eq.{category}")
        if location:
            filters.append(f"location=eq.{location}")

        if filters:
            url += "?" + "&".join(filters)

        res = requests.get(url, headers=HEADERS)
        assets = res.json() if res.status_code == 200 else []
        if res.status_code != 200:
            messages.error(request, "Gagal mengambil daftar aset.")

        res_categories = requests.get(f'{SUPABASE_URL}/rest/v1/categories', headers=HEADERS)
        categories = res_categories.json() if res_categories.status_code == 200 else []

        res_locations = requests.get(f'{SUPABASE_URL}/rest/v1/locations', headers=HEADERS)
        locations = res_locations.json() if res_locations.status_code == 200 else []

        page = request.GET.get('page', 1)
        items_per_page = 10
        paginator = Paginator(assets, items_per_page)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        query_params = request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        query_string = query_params.urlencode()

        return render(request, 'assets/asset_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'search_query': search_query,
            'categories': categories,
            'locations': locations,
            'selected_category': category,
            'selected_location': location,
            'query_string': query_string,
            'user': user
        })

# 🔥 Tambah Aset
class AssetCreateView(View):
    def get(self, request):
        user = request.session.get('user')
        return render(request, 'assets/asset_create.html', {'user': user})

    def post(self, request):
        user = request.session.get('user')

        name = request.POST.get('name')
        location = request.POST.get('location')
        code = request.POST.get('code')

        if not all([name, location, code]):
            messages.error(request, "Semua field harus diisi.")
            return render(request, 'assets/asset_create.html', {'user': user})

        data = {
            "name": name,
            "location": location,
            "code": code
        }

        res = requests.post(f'{SUPABASE_URL}/rest/v1/assets', headers=HEADERS, json=data)
        if res.status_code == 201:
            messages.success(request, "Aset berhasil ditambahkan.")
            return redirect('asset_list')

        messages.error(request, "Gagal menambahkan aset.")
        return render(request, 'assets/asset_create.html', {'user': user})

# 🔥 Edit Aset
class AssetEditView(View):
    def get(self, request, asset_id):
        user = request.session.get('user')

        res = requests.get(f'{SUPABASE_URL}/rest/v1/assets?id=eq.{asset_id}', headers=HEADERS)
        asset = res.json()[0] if res.status_code == 200 and res.json() else None

        if not asset:
            messages.error(request, "Aset tidak ditemukan.")
            return redirect('asset_list')

        return render(request, 'assets/asset_edit.html', {'asset': asset, 'user': user})

    def post(self, request, asset_id):
        user = request.session.get('user')

        name = request.POST.get('name')
        location = request.POST.get('location')

        if not all([name, location]):
            messages.error(request, "Semua field harus diisi.")
            return redirect('asset_edit', asset_id=asset_id)

        data = {
            "name": name,
            "location": location
        }

        res = requests.patch(f'{SUPABASE_URL}/rest/v1/assets?id=eq.{asset_id}', headers=HEADERS, json=data)
        if res.status_code == 204:
            messages.success(request, "Aset berhasil diperbarui.")
            return redirect('asset_list')

        messages.error(request, "Gagal memperbarui aset.")
        return redirect('asset_edit', asset_id=asset_id)

# 🔥 Mutasi Aset
class AssetMoveView(View):
    def get(self, request, asset_id):
        user = request.session.get('user')

        res = requests.get(f'{SUPABASE_URL}/rest/v1/assets?id=eq.{asset_id}', headers=HEADERS)
        asset = res.json()[0] if res.status_code == 200 and res.json() else None

        if not asset:
            messages.error(request, "Aset tidak ditemukan.")
            return redirect('asset_list')

        return render(request, 'assets/asset_move.html', {'asset': asset, 'user': user})

    def post(self, request, asset_id):
        user = request.session.get('user')

        new_location = request.POST.get('location')

        if not new_location:
            messages.error(request, "Lokasi baru harus diisi.")
            return redirect('asset_move', asset_id=asset_id)

        data = {
            "location": new_location
        }

        res_update = requests.patch(f'{SUPABASE_URL}/rest/v1/assets?id=eq.{asset_id}', headers=HEADERS, json=data)

        history_data = {
            "asset_id": asset_id,
            "new_location": new_location,
            "moved_by": user.get('full_name')
        }
        res_history = requests.post(f'{SUPABASE_URL}/rest/v1/asset_histories', headers=HEADERS, json=history_data)

        if res_update.status_code == 204 and res_history.status_code == 201:
            messages.success(request, "Aset berhasil dipindahkan.")
            return redirect('asset_list')

        messages.error(request, "Gagal memindahkan aset.")
        return redirect('asset_move', asset_id=asset_id)

# 🔥 History Mutasi Aset
class AssetHistoryView(View):
    def get(self, request, asset_id):
        user = request.session.get('user')

        res = requests.get(f'{SUPABASE_URL}/rest/v1/asset_histories?asset_id=eq.{asset_id}', headers=HEADERS)
        histories = res.json() if res.status_code == 200 else []

        if res.status_code != 200:
            messages.error(request, "Gagal mengambil riwayat aset.")

        return render(request, 'assets/asset_history.html', {'histories': histories, 'user': user})

# 🔥 Hapus Aset Satu
class AssetDeleteView(View):
    def post(self, request, asset_id):
        user = request.session.get('user')

        if user.get('role') != 'admin':
            return redirect('login')

        res = requests.delete(f'{SUPABASE_URL}/rest/v1/assets?id=eq.{asset_id}', headers=HEADERS)
        if res.status_code == 204:
            messages.success(request, "Aset berhasil dihapus.")
        else:
            messages.error(request, "Gagal menghapus aset.")
        return redirect('asset_list')

# 📦 Tambahan Export Excel, Export PDF, Import Excel

@session_login_required
def asset_export_excel(request):
    user = request.session.get('user')
    res = requests.get(f'{SUPABASE_URL}/rest/v1/assets', headers=HEADERS)
    assets = res.json() if res.status_code == 200 else []

    if not assets:
        messages.error(request, "Tidak ada data aset untuk diexport.")
        return redirect('asset_list')

    df = pd.DataFrame(assets)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Assets')

    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="assets.xlsx"'
    return response

@session_login_required
def asset_export_pdf(request):
    user = request.session.get('user')
    res = requests.get(f'{SUPABASE_URL}/rest/v1/assets', headers=HEADERS)
    assets = res.json() if res.status_code == 200 else []

    if not assets:
        messages.error(request, "Tidak ada data aset untuk diexport.")
        return redirect('asset_list')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="assets.pdf"'

    p = canvas.Canvas(response)
    width, height = 595, 842  # Ukuran A4
    margin = 50
    y = height - margin

    # Judul
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y, "Daftar Aset")
    y -= 40

    # Header Tabel
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "No")
    p.drawString(margin + 40, y, "Nama")
    p.drawString(margin + 200, y, "Lokasi")
    p.drawString(margin + 350, y, "Kode")
    y -= 20
    p.line(margin, y, width - margin, y)
    y -= 10

    p.setFont("Helvetica", 11)

    for idx, asset in enumerate(assets, start=1):
        if y <= 50:
            p.showPage()
            y = height - margin
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width / 2, y, "Daftar Aset (Lanjutan)")
            y -= 40
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y, "No")
            p.drawString(margin + 40, y, "Nama")
            p.drawString(margin + 200, y, "Lokasi")
            p.drawString(margin + 350, y, "Kode")
            y -= 20
            p.line(margin, y, width - margin, y)
            y -= 10
            p.setFont("Helvetica", 11)

        p.drawString(margin, y, str(idx))
        p.drawString(margin + 40, y, asset.get('name', ''))
        p.drawString(margin + 200, y, asset.get('location', ''))
        p.drawString(margin + 350, y, asset.get('code', ''))
        y -= 20

    p.showPage()
    p.save()

    return response

@session_login_required
@csrf_exempt
def asset_import_excel(request):
    user = request.session.get('user')
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)
            required_columns = {'name', 'location', 'code'}
            if not required_columns.issubset(df.columns):
                messages.error(request, "File Excel harus memiliki kolom: name, location, code.")
                return redirect('asset_list')

            success_count = 0
            for _, row in df.iterrows():
                data = {
                    "name": row['name'],
                    "location": row['location'],
                    "code": row['code'],
                }
                res = requests.post(f'{SUPABASE_URL}/rest/v1/assets', headers=HEADERS, json=data)
                if res.status_code == 201:
                    success_count += 1

            messages.success(request, f"{success_count} aset berhasil diimport.")
        except Exception as e:
            messages.error(request, f"Gagal mengimport data: {str(e)}")
        return redirect('asset_list')

    return render(request, 'assets/asset_import.html', {'user': user})
