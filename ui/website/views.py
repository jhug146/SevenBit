import csv
import io
import json
import mimetypes
import os
import threading

from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.shortcuts import render, redirect

from ui.website.state import state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _path_to_url(path: str) -> str:
    """Convert a local image path to a URL served by the /img/ view."""
    if not path:
        return ""
    if "http" in path:
        return path
    path = path.replace("\\", "/")
    # Handle absolute Windows paths (e.g. C:/...)
    if len(path) > 1 and path[1] == ":":
        try:
            rel = os.path.relpath(path.replace("/", os.sep), os.getcwd())
            path = rel.replace("\\", "/")
        except ValueError:
            return ""
    path = path.lstrip("/")
    return f"/img/{path}"


def _run_in_thread(fn, *args):
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Page views
# ---------------------------------------------------------------------------

def items(request):
    item_rows = []
    if state.item_list and state.item_list.items:
        outlined_set = (
            set(state.outlined_items)
            if isinstance(state.outlined_items, list)
            else {state.outlined_items}
        )
        for i, item in enumerate(state.item_list.items):
            first_image = ""
            if item.images:
                paths = [p for p in item.images.split(";") if p]
                if paths:
                    first_image = _path_to_url(paths[0])
            outlined_class = ""
            if i in outlined_set:
                outlined_class = "row-outlined-red" if state.outlined_red else "row-outlined-blue"
            item_rows.append({
                "n": i,
                "title": item.title,
                "sku": item.sku,
                "price": item.price,
                "image_url": first_image,
                "outlined_class": outlined_class,
            })

    upload_mode_ctx = None
    if state.upload_changer:
        uc = state.upload_changer
        allowed = (
            state.item_type.accounts.allowed_destinations
            if state.item_type else None
        )
        ebay_sites = []
        for i, (label, opt) in enumerate(zip(uc.ebay_labels, uc.ebay_options)):
            if allowed is None or opt in allowed:
                ebay_sites.append({
                    "label": label,
                    "opt": opt,
                    "checked": bool(uc.upload_state[i]),
                })
        website_dests = []
        for dest in uc._website_dests:
            if allowed is None or dest.name in allowed:
                website_dests.append({
                    "label": dest.label,
                    "name": dest.name,
                    "checked": uc._website_state.get(dest.name, False),
                })
        upload_mode_ctx = {
            "ebay_sites": ebay_sites,
            "website_dests": website_dests,
            "fast_images": uc.fast_images,
            "download_images": uc.download_images,
        }

    return render(request, "items.html", {
        "title": state.title,
        "item_rows": item_rows,
        "upload_mode": upload_mode_ctx,
    })


def import_csv(request):
    if request.method == "POST" and state.item_list is not None:
        f = request.FILES.get("csv_file")
        if f:
            raw = f.read()
            try:
                content = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                content = raw.decode("latin-1")
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            if rows:
                headers = rows[0]
                data = rows[1:] if len(rows) > 1 else []
                state.item_list.load(headers, data)
    return redirect("items")


def item_detail(request, n):
    if not (state.item_list and state.item_list.items) or n >= len(state.item_list.items):
        return redirect("items")

    item = state.item_list.items[n]
    display_order = state.item_type.upload.display_order if state.item_type else []
    count = len(state.item_list.items)

    image_paths = [p for p in item.images.split(";") if p] if item.images else []
    images = [{"url": _path_to_url(p), "path": p} for p in image_paths]

    all_keys = item.keys()
    displayed_specifics = [
        (k, item[k], k[3:])
        for k in all_keys
        if k in display_order
    ]

    return render(request, "item_detail.html", {
        "title": state.title,
        "item": item,
        "n": n,
        "count": count,
        "prev_n": n - 1 if n > 0 else None,
        "next_n": n + 1 if n < count - 1 else None,
        "images": images,
        "image_paths_json": json.dumps(image_paths),
        "displayed_specifics": displayed_specifics,
    })


def save_item(request, n):
    if request.method == "POST" and state.item_list and state.item_list.items:
        if n < len(state.item_list.items):
            item = state.item_list.items[n]
            display_order = state.item_type.upload.display_order if state.item_type else []

            changes = {}
            for field in ("Title", "Price", "SKU"):
                val = request.POST.get(field.lower())
                if val is not None:
                    changes[field] = val

            i = 1
            while f"condition_{i}" in request.POST:
                changes[f"Condition {i}"] = request.POST[f"condition_{i}"]
                i += 1

            for k in display_order:
                val = request.POST.get(f"specific_{k}")
                if val is not None:
                    changes[k] = val

            if "images" in request.POST:
                changes["Path"] = request.POST["images"]

            for key, value in changes.items():
                item[key] = value

    return redirect("item_detail", n=n)


def upload_item(request, n):
    if request.method == "POST" and state.item_list and state.item_list.items and state.upload:
        if n < len(state.item_list.items):
            sku = state.item_list.items[n].sku
            _run_in_thread(state.upload.upload_skus, sku)
            return redirect("upload_display")
    return redirect("item_detail", n=n)


def upload_display(request):
    return render(request, "upload.html", {"title": state.title})


def start_upload(request):
    if request.method == "POST" and state.upload:
        mode = request.POST.get("mode", "normal")
        if mode == "normal":
            _run_in_thread(state.upload.upload_all)
        elif mode == "specific":
            skus = request.POST.get("skus", "")
            _run_in_thread(state.upload.upload_skus, skus)
        elif mode == "range":
            start_sku = request.POST.get("start_sku", "")
            end_sku = request.POST.get("end_sku", "")
            _run_in_thread(state.upload.upload_from, start_sku, end_sku)
        return redirect("upload_display")
    return redirect("items")


def stop_upload(request):
    if request.method == "POST" and state.upload:
        state.upload.set_upload(True)
    return redirect("upload_display")


def upload_stream(request):
    """SSE endpoint — streams upload status events to the browser."""
    def event_stream():
        while True:
            try:
                event = state.sse_queue.get(timeout=15)
                yield f"data: {json.dumps(event)}\n\n"
            except Exception:
                yield 'data: {"type":"heartbeat"}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ---------------------------------------------------------------------------
# Modal action endpoints (return JSON)
# ---------------------------------------------------------------------------

def switch_account(request):
    if request.method == "POST" and state.actions:
        name = request.POST.get("name", "").strip()
        if state.actions.switch_account(name):
            state.actions.get_status()
            return JsonResponse({"success": True, "title": state.title})
        return JsonResponse({"success": False, "error": f'Account "{name}" not found'})
    return JsonResponse({"success": False})


def switch_item_type(request):
    if request.method == "POST" and state.actions:
        name = request.POST.get("name", "").strip()
        try:
            state.actions.switch_item_type(name)
            state.actions.get_status()
            return JsonResponse({"success": True, "title": state.title})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False})


def update_upload_mode(request):
    if request.method == "POST" and state.upload_changer:
        uc = state.upload_changer
        for i, opt in enumerate(uc.ebay_options):
            uc.upload_state[i] = 1 if request.POST.get(f"ebay_{opt}") else 0
        for dest in uc._website_dests:
            uc._website_state[dest.name] = bool(request.POST.get(f"dest_{dest.name}"))
        uc.fast_images = bool(request.POST.get("fast_images"))
        uc.download_images = bool(request.POST.get("download_images"))
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


def download_items(request):
    if request.method == "POST" and state.get_items:
        raw = request.POST.get("item_numbers", "").strip()
        if state.get_items.search_from_input(raw):
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "Invalid numbers entered"})
    return JsonResponse({"success": False})


def get_status(request):
    if state.actions:
        state.actions.get_status()
    return JsonResponse({"title": state.title})


# ---------------------------------------------------------------------------
# Image serving
# ---------------------------------------------------------------------------

def serve_image(request, image_path):
    full_path = os.path.normpath(os.path.join(os.getcwd(), image_path))
    project_root = os.path.abspath(os.getcwd())
    # Security: block path traversal outside project root
    if not (full_path.startswith(project_root + os.sep) or full_path == project_root):
        return HttpResponse(status=403)
    if not os.path.isfile(full_path):
        return HttpResponse(status=404)
    content_type, _ = mimetypes.guess_type(full_path)
    with open(full_path, "rb") as f:
        return HttpResponse(f.read(), content_type=content_type or "image/jpeg")
