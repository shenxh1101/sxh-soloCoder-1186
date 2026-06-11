import os
import io
import uuid
import tempfile
import json
import base64
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, abort, current_app, url_for, send_from_directory, redirect
from werkzeug.utils import secure_filename
from PIL import Image

from utils import (
    allowed_file, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_EXTENSIONS,
    get_file_hash, save_uploaded_file, extract_zip, parse_size_str
)
from icon_generator import ProcessingOptions, CropOptions
from icon_service import generate_icon_set, prepare_image_for_crop
from image_processor import crop_image, image_to_bytes
from cache import CacheManager
from zip_exporter import create_zip_from_directory, create_zip_from_multiple_directories
from history_manager import HistoryManager, create_history_record

main_bp = Blueprint('main', __name__)

def get_cache_manager():
    if not hasattr(current_app, 'cache_manager'):
        current_app.cache_manager = CacheManager(current_app.config['CACHE_FOLDER'])
    return current_app.cache_manager

def get_history_manager():
    if not hasattr(current_app, 'history_manager'):
        history_file = os.path.join(current_app.config['CACHE_FOLDER'], 'history.json')
        current_app.history_manager = HistoryManager(history_file, max_records=50)
    return current_app.history_manager

def parse_options_from_request(request) -> ProcessingOptions:
    form = request.form if request.method == 'POST' else request.args
    
    corner_radius = int(form.get('corner_radius', 0) or 0)
    background_color = form.get('background_color', '').strip() or None
    shadow = form.get('shadow', 'false').lower() in ['true', '1', 'yes']
    shadow_blur = int(form.get('shadow_blur', 10) or 10)
    
    shadow_offset_x = int(form.get('shadow_offset_x', 0) or 0)
    shadow_offset_y = int(form.get('shadow_offset_y', 4) or 4)
    shadow_offset = (shadow_offset_x, shadow_offset_y)
    
    shadow_color = form.get('shadow_color', 'rgba(0, 0, 0, 0.3)').strip()
    
    custom_sizes = []
    sizes_input = form.get('custom_sizes', '').strip()
    if sizes_input:
        for size_str in sizes_input.split(','):
            size = parse_size_str(size_str)
            if size:
                custom_sizes.append(size)
    sizes_list = form.getlist('custom_sizes[]') if hasattr(form, 'getlist') else []
    for size_str in sizes_list:
        size = parse_size_str(size_str.strip())
        if size and size not in custom_sizes:
            custom_sizes.append(size)
    
    custom_filenames = {}
    for key in form:
        if key.startswith('filename_'):
            filename_key = key[len('filename_'):]
            value = form.get(key, '').strip()
            if value:
                custom_filenames[filename_key] = value
    
    filenames_input = form.get('custom_filenames', '').strip()
    if filenames_input:
        try:
            parsed = json.loads(filenames_input)
            for k, v in parsed.items():
                if v:
                    custom_filenames[k] = v
        except:
            pass
    
    app_name = form.get('app_name', 'My App').strip() or 'My App'
    app_short_name = form.get('app_short_name', 'App').strip() or 'App'
    theme_color = form.get('theme_color', '#ffffff').strip() or '#ffffff'
    background_color_manifest = form.get('background_color_manifest', theme_color).strip() or theme_color
    
    crop_enabled = form.get('crop_enabled', 'false').lower() in ['true', '1', 'yes']
    crop_x = int(form.get('crop_x', 0) or 0)
    crop_y = int(form.get('crop_y', 0) or 0)
    crop_width = int(form.get('crop_width', 0) or 0)
    crop_height = int(form.get('crop_height', 0) or 0)
    crop_scale = float(form.get('crop_scale', 1.0) or 1.0)
    crop_mode = form.get('crop_mode', 'cover').strip() or 'cover'
    
    crop = CropOptions(
        enabled=crop_enabled,
        x=crop_x,
        y=crop_y,
        width=crop_width,
        height=crop_height,
        scale=crop_scale,
        mode=crop_mode
    )
    
    return ProcessingOptions(
        corner_radius=corner_radius,
        background_color=background_color,
        shadow=shadow,
        shadow_blur=shadow_blur,
        shadow_offset=shadow_offset,
        shadow_color=shadow_color,
        custom_sizes=custom_sizes,
        custom_filenames=custom_filenames,
        app_name=app_name,
        app_short_name=app_short_name,
        theme_color=theme_color,
        background_color_manifest=background_color_manifest,
        crop=crop
    )

def options_to_dict(options: ProcessingOptions) -> dict:
    return {
        'corner_radius': options.corner_radius,
        'background_color': options.background_color,
        'shadow': options.shadow,
        'shadow_blur': options.shadow_blur,
        'shadow_offset': list(options.shadow_offset),
        'shadow_color': options.shadow_color,
        'custom_sizes': [list(s) for s in options.custom_sizes],
        'custom_filenames': options.custom_filenames,
        'app_name': options.app_name,
        'app_short_name': options.app_short_name,
        'theme_color': options.theme_color,
        'background_color_manifest': options.background_color_manifest,
        'crop': {
            'enabled': options.crop.enabled,
            'x': options.crop.x,
            'y': options.crop.y,
            'width': options.crop.width,
            'height': options.crop.height,
            'scale': options.crop.scale,
            'mode': options.crop.mode
        }
    }

def get_batch_results(batch_id):
    return current_app.config.get('BATCH_RESULTS', {}).get(batch_id)

def set_batch_results(batch_id, data):
    current_app.config.setdefault('BATCH_RESULTS', {})
    current_app.config['BATCH_RESULTS'][batch_id] = data

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/history')
def history():
    history_mgr = get_history_manager()
    records = history_mgr.get_all()
    return render_template('history.html', records=records)

@main_bp.route('/compare')
def compare_page():
    ids_str = request.args.get('ids', '')
    ids = [x.strip() for x in ids_str.split(',') if x.strip()]
    history_mgr = get_history_manager()
    records = []
    for rid in ids:
        rec = history_mgr.get_by_id(rid)
        if rec:
            rec_dict = {
                'id': rec.id,
                'original_name': rec.original_name,
                'created_at': rec.created_at,
                'cached': rec.cached,
                'file_count': rec.file_count,
                'options': rec.options if isinstance(rec.options, dict) else {},
                'files_list': []
            }
            cache_mgr = get_cache_manager()
            cached = cache_mgr.get(rec.cache_key)
            if cached and 'files' in cached:
                rec_dict['files_list'] = sorted([f.get('filename', k) for k, f in cached['files'].items()])
            records.append(rec_dict)
    return render_template('compare.html', records=records)

@main_bp.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    options = parse_options_from_request(request)
    
    image_paths = []
    is_batch = False
    
    for file_storage in files:
        if not allowed_file(file_storage.filename):
            continue
        
        filename = secure_filename(file_storage.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'zip':
            is_batch = True
            zip_path = save_uploaded_file(file_storage, current_app.config['UPLOAD_FOLDER'])
            extract_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
            os.makedirs(extract_dir, exist_ok=True)
            extracted = extract_zip(zip_path, extract_dir)
            image_paths.extend(extracted)
            os.remove(zip_path)
        else:
            filepath = save_uploaded_file(file_storage, current_app.config['UPLOAD_FOLDER'])
            image_paths.append(filepath)
    
    if not image_paths:
        return jsonify({'error': 'No valid images found'}), 400
    
    upload_id = str(uuid.uuid4())
    upload_data = {
        'image_paths': image_paths,
        'options': options,
        'is_batch': is_batch,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    current_app.config.setdefault('UPLOAD_SESSIONS', {})
    current_app.config['UPLOAD_SESSIONS'][upload_id] = upload_data
    
    skip_crop = request.form.get('skip_crop', 'false').lower() in ['true', '1', 'yes']
    
    if skip_crop:
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'skip_crop': True
        })
    
    first_image = image_paths[0]
    with Image.open(first_image) as img:
        img_width, img_height = img.size
    
    return jsonify({
        'success': True,
        'upload_id': upload_id,
        'image_count': len(image_paths),
        'is_batch': is_batch,
        'first_image': {
            'name': os.path.basename(first_image),
            'width': img_width,
            'height': img_height
        },
        'crop_url': url_for('main.crop_page', upload_id=upload_id)
    })

@main_bp.route('/crop/<upload_id>')
def crop_page(upload_id):
    upload_sessions = current_app.config.get('UPLOAD_SESSIONS', {})
    upload_data = upload_sessions.get(upload_id)
    
    if not upload_data:
        abort(404)
    
    first_image = upload_data['image_paths'][0]
    image_name = os.path.basename(first_image)
    
    with Image.open(first_image) as img:
        img_width, img_height = img.size
    
    return render_template('crop.html',
                           upload_id=upload_id,
                           image_name=image_name,
                           image_width=img_width,
                           image_height=img_height,
                           image_count=len(upload_data['image_paths']),
                           is_batch=upload_data['is_batch'])

@main_bp.route('/api/crop-image/<upload_id>')
def crop_image_api(upload_id):
    upload_sessions = current_app.config.get('UPLOAD_SESSIONS', {})
    upload_data = upload_sessions.get(upload_id)
    
    if not upload_data:
        abort(404)
    
    idx = int(request.args.get('index', 0))
    image_paths = upload_data['image_paths']
    if idx < 0 or idx >= len(image_paths):
        idx = 0
    target_image = image_paths[idx]
    
    x = int(request.args.get('x', 0))
    y = int(request.args.get('y', 0))
    width = int(request.args.get('width', 0))
    height = int(request.args.get('height', 0))
    scale = float(request.args.get('scale', 1.0))
    mode = request.args.get('mode', 'cover')
    preview_size = int(request.args.get('preview_size', 200))
    
    img = prepare_image_for_crop(target_image)
    
    if width > 0 and height > 0:
        cropped = crop_image(img, x, y, width, height, scale, mode)
    else:
        cropped = img
    
    cropped.thumbnail((preview_size, preview_size), Image.LANCZOS)
    
    buf = io.BytesIO()
    cropped.save(buf, format='PNG')
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@main_bp.route('/api/original-image/<upload_id>')
def original_image_api(upload_id):
    upload_sessions = current_app.config.get('UPLOAD_SESSIONS', {})
    upload_data = upload_sessions.get(upload_id)
    
    if not upload_data:
        abort(404)
    
    idx = int(request.args.get('index', 0))
    image_paths = upload_data['image_paths']
    if idx < 0 or idx >= len(image_paths):
        idx = 0
    target_image = image_paths[idx]
    
    img = Image.open(target_image)
    max_size = 800
    if img.size[0] > max_size or img.size[1] > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@main_bp.route('/api/upload-info/<upload_id>')
def upload_info_api(upload_id):
    upload_sessions = current_app.config.get('UPLOAD_SESSIONS', {})
    upload_data = upload_sessions.get(upload_id)
    
    if not upload_data:
        return jsonify({'error': 'Upload session not found'}), 404
    
    images = []
    for i, p in enumerate(upload_data['image_paths']):
        try:
            with Image.open(p) as img:
                w, h = img.size
            images.append({
                'index': i,
                'name': os.path.basename(p),
                'width': w,
                'height': h
            })
        except:
            pass
    
    return jsonify({
        'success': True,
        'upload_id': upload_id,
        'image_count': len(images),
        'images': images
    })

@main_bp.route('/generate', methods=['POST'])
def generate():
    data = request.get_json() if request.is_json else request.form
    upload_id = data.get('upload_id')
    
    upload_sessions = current_app.config.get('UPLOAD_SESSIONS', {})
    upload_data = upload_sessions.get(upload_id)
    
    if not upload_data:
        return jsonify({'error': 'Upload session not found'}), 404
    
    options = parse_options_from_request(request)
    base_options = upload_data.get('options')
    shared_options = None

    if base_options:
        if hasattr(base_options, '__dict__'):
            shared_options = base_options
        elif isinstance(base_options, dict):
            from icon_generator import ProcessingOptions, CropOptions
            shared_options = ProcessingOptions(
                corner_radius=base_options.get('corner_radius', 0),
                background_color=base_options.get('background_color'),
                shadow=base_options.get('shadow', False),
                shadow_blur=base_options.get('shadow_blur', 10),
                shadow_offset=tuple(base_options.get('shadow_offset', [0, 4])),
                shadow_color=base_options.get('shadow_color', 'rgba(0, 0, 0, 0.3)'),
                custom_sizes=[tuple(s) for s in base_options.get('custom_sizes', [])],
                custom_filenames=base_options.get('custom_filenames', {}),
                app_name=base_options.get('app_name', 'My App'),
                app_short_name=base_options.get('app_short_name', 'App'),
                theme_color=base_options.get('theme_color', '#ffffff'),
                background_color_manifest=base_options.get('background_color_manifest', '#ffffff'),
                crop=CropOptions(**base_options.get('crop', {})) if base_options.get('crop') else CropOptions()
            )

    per_image_crops = None
    crops_raw = data.get('crops')
    if crops_raw:
        try:
            if isinstance(crops_raw, str):
                per_image_crops = json.loads(crops_raw)
            elif isinstance(crops_raw, list):
                per_image_crops = crops_raw
        except:
            per_image_crops = None

    def make_options_for_image(idx, fallback_crop):
        from icon_generator import ProcessingOptions, CropOptions
        src = shared_options or options
        if per_image_crops and isinstance(per_image_crops, list) and idx < len(per_image_crops) and per_image_crops[idx]:
            c = per_image_crops[idx]
            crop = CropOptions(
                enabled=bool(c.get('enabled', True)),
                x=int(c.get('x', 0)),
                y=int(c.get('y', 0)),
                width=int(c.get('width', 0)),
                height=int(c.get('height', 0)),
                scale=float(c.get('scale', 1.0)),
                mode=c.get('mode', 'cover')
            )
        else:
            crop = fallback_crop
        if hasattr(src, '__dict__'):
            return ProcessingOptions(
                corner_radius=src.corner_radius,
                background_color=src.background_color,
                shadow=src.shadow,
                shadow_blur=src.shadow_blur,
                shadow_offset=src.shadow_offset,
                shadow_color=src.shadow_color,
                custom_sizes=list(src.custom_sizes),
                custom_filenames=dict(src.custom_filenames),
                app_name=src.app_name,
                app_short_name=src.app_short_name,
                theme_color=src.theme_color,
                background_color_manifest=src.background_color_manifest,
                crop=crop
            )
        return ProcessingOptions(crop=crop) if not crop.enabled else ProcessingOptions(crop=crop)
    
    cache_mgr = get_cache_manager()
    history_mgr = get_history_manager()
    
    image_paths = upload_data['image_paths']
    results = []
    temp_output_dirs = {}
    
    for i, image_path in enumerate(image_paths):
        try:
            img_opts = make_options_for_image(i, options.crop)
            
            with open(image_path, 'rb') as f:
                file_content = f.read()
            file_hash = get_file_hash(file_content)
            cache_key = cache_mgr.get_cache_key(file_hash, img_opts)
            original_name = os.path.basename(image_path)
            
            cached = cache_mgr.get(cache_key)
            if cached:
                result_data = {
                    'original_name': original_name,
                    'file_hash': file_hash,
                    'cache_key': cache_key,
                    'cached': True,
                    'files': cached['files'],
                    'cache_dir': cached['cache_dir']
                }
                results.append(result_data)
                temp_output_dirs[original_name] = cached['cache_dir']
                
                record = create_history_record(
                    record_id=str(uuid.uuid4()),
                    original_name=original_name,
                    file_hash=file_hash,
                    cache_key=cache_key,
                    options=options_to_dict(img_opts),
                    cached=True,
                    file_count=len(cached['files'])
                )
                history_mgr.add_record(record)
                continue
            
            output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], str(uuid.uuid4()))
            os.makedirs(output_dir, exist_ok=True)
            
            generated_files = generate_icon_set(image_path, img_opts, output_dir)
            
            cache_mgr.set(cache_key, generated_files, output_dir, original_name)
            
            files_info = {}
            for k, v in generated_files.items():
                if 'filename' in v:
                    files_info[k] = {
                        'filename': v['filename'],
                        'type': v.get('type', ''),
                        'size': v.get('size'),
                        'sizes': v.get('sizes')
                    }
            
            result_data = {
                'original_name': original_name,
                'file_hash': file_hash,
                'cache_key': cache_key,
                'cached': False,
                'files': files_info,
                'cache_dir': output_dir
            }
            results.append(result_data)
            temp_output_dirs[original_name] = output_dir
            
            record = create_history_record(
                record_id=str(uuid.uuid4()),
                original_name=original_name,
                file_hash=file_hash,
                cache_key=cache_key,
                options=options_to_dict(img_opts),
                cached=False,
                file_count=len(files_info)
            )
            history_mgr.add_record(record)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({
                'original_name': os.path.basename(image_path),
                'error': str(e)
            })
        finally:
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass
    
    if upload_id in upload_sessions:
        del upload_sessions[upload_id]
    
    batch_id = str(uuid.uuid4())
    final_options = shared_options or options
    set_batch_results(batch_id, {
        'results': results,
        'output_dirs': temp_output_dirs,
        'options': final_options
    })
    
    return jsonify({
        'success': True,
        'batch_id': batch_id,
        'count': len(results),
        'is_batch': len(results) > 1,
        'results': results,
        'preview_url': url_for('main.preview', batch_id=batch_id)
    })

@main_bp.route('/preview/<batch_id>')
def preview(batch_id):
    batch_data = get_batch_results(batch_id)
    if not batch_data:
        abort(404)
    
    options = batch_data.get('options')
    if options:
        if isinstance(options, dict):
            options_dict = options
        else:
            options_dict = options_to_dict(options)
    else:
        options_dict = {}
    
    return render_template('preview.html', 
                           batch_id=batch_id, 
                           results=batch_data['results'],
                           is_batch=len(batch_data['results']) > 1,
                           options=options_dict)

@main_bp.route('/preview/file/<batch_id>/<original_name>/<filename>')
def preview_file(batch_id, original_name, filename):
    batch_data = get_batch_results(batch_id)
    if not batch_data:
        abort(404)
    
    output_dir = batch_data['output_dirs'].get(original_name)
    if not output_dir:
        abort(404)
    
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        abort(404)
    
    return send_from_directory(output_dir, filename)

@main_bp.route('/download/<batch_id>')
def download(batch_id):
    batch_data = get_batch_results(batch_id)
    if not batch_data:
        abort(404)
    
    output_dirs = batch_data['output_dirs']
    
    if len(output_dirs) == 1:
        original_name = list(output_dirs.keys())[0]
        source_dir = list(output_dirs.values())[0]
        zip_bytes = create_zip_from_directory(source_dir)
        download_name = f"{os.path.splitext(original_name)[0]}_icons.zip"
    else:
        zip_bytes = create_zip_from_multiple_directories(output_dirs)
        download_name = "icons_batch.zip"
    
    zip_io = io.BytesIO(zip_bytes)
    return send_file(
        zip_io,
        mimetype='application/zip',
        as_attachment=True,
        download_name=download_name
    )

@main_bp.route('/download/single/<batch_id>/<original_name>')
def download_single(batch_id, original_name):
    batch_data = get_batch_results(batch_id)
    if not batch_data:
        abort(404)
    
    output_dir = batch_data['output_dirs'].get(original_name)
    if not output_dir:
        abort(404)
    
    zip_bytes = create_zip_from_directory(output_dir)
    download_name = f"{os.path.splitext(original_name)[0]}_icons.zip"
    
    zip_io = io.BytesIO(zip_bytes)
    return send_file(
        zip_io,
        mimetype='application/zip',
        as_attachment=True,
        download_name=download_name
    )

@main_bp.route('/history/preview/<record_id>')
def history_preview(record_id):
    history_mgr = get_history_manager()
    record = history_mgr.get_by_id(record_id)
    
    if not record:
        abort(404)
    
    cache_mgr = get_cache_manager()
    cached = cache_mgr.get(record.cache_key)
    
    if not cached:
        abort(404)
    
    batch_id = f"history_{record_id}"
    set_batch_results(batch_id, {
        'results': [{
            'original_name': record.original_name,
            'file_hash': record.file_hash,
            'cache_key': record.cache_key,
            'cached': True,
            'files': cached['files'],
            'cache_dir': cached['cache_dir']
        }],
        'output_dirs': {record.original_name: cached['cache_dir']},
        'options': record.options
    })
    
    return redirect(url_for('main.preview', batch_id=batch_id))

@main_bp.route('/history/download/<record_id>')
def history_download(record_id):
    history_mgr = get_history_manager()
    record = history_mgr.get_by_id(record_id)
    
    if not record:
        abort(404)
    
    cache_mgr = get_cache_manager()
    cached = cache_mgr.get(record.cache_key)
    
    if not cached:
        abort(404)
    
    zip_bytes = create_zip_from_directory(cached['cache_dir'])
    download_name = f"{os.path.splitext(record.original_name)[0]}_icons.zip"
    
    zip_io = io.BytesIO(zip_bytes)
    return send_file(
        zip_io,
        mimetype='application/zip',
        as_attachment=True,
        download_name=download_name
    )

@main_bp.route('/api/history/delete/<record_id>', methods=['POST'])
def delete_history(record_id):
    history_mgr = get_history_manager()
    success = history_mgr.delete_record(record_id)
    return jsonify({'success': success})

@main_bp.route('/api/cache/stats')
def cache_stats():
    cache_mgr = get_cache_manager()
    stats = cache_mgr.get_stats()
    
    history_mgr = get_history_manager()
    stats['history_count'] = history_mgr.count()
    
    return jsonify(stats)

@main_bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    cache_mgr = get_cache_manager()
    cache_mgr.clear()
    
    history_mgr = get_history_manager()
    history_mgr.clear_all()
    
    return jsonify({'success': True, 'message': 'Cache and history cleared'})

@main_bp.route('/api/history/detail/<record_id>')
def history_detail(record_id):
    history_mgr = get_history_manager()
    record = history_mgr.get_by_id(record_id)
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    options_dict = record.options
    if hasattr(record, 'options') and not isinstance(record.options, dict):
        options_dict = options_to_dict(record.options)
    
    return jsonify({
        'success': True,
        'record': {
            'id': record.id,
            'original_name': record.original_name,
            'created_at': record.created_at,
            'file_count': record.file_count,
            'from_cache': record.cached,
            'cache_key': record.cache_key,
            'file_hash': record.file_hash,
            'options': options_dict
        }
    })

@main_bp.route('/api/reuse-template/<record_id>')
def reuse_template(record_id):
    history_mgr = get_history_manager()
    record = history_mgr.get_by_id(record_id)
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    options_dict = record.options
    if hasattr(record, 'options') and not isinstance(record.options, dict):
        options_dict = options_to_dict(record.options)
    
    return jsonify({
        'success': True,
        'template': options_dict
    })

@main_bp.route('/download/filtered/<batch_id>', methods=['POST'])
def download_filtered(batch_id):
    batch_data = get_batch_results(batch_id)
    if not batch_data:
        abort(404)
    
    data = request.get_json() if request.is_json else request.form
    selected_files = data.getlist('files') if hasattr(data, 'getlist') else data.get('files', [])
    if isinstance(selected_files, str):
        selected_files = [selected_files]
    custom_name = data.get('zip_name', '').strip()
    
    if isinstance(data, dict) and 'files' in data and isinstance(data['files'], str):
        selected_files = data['files'].split(',')
    
    include_manifest = data.get('include_manifest', 'true').lower() in ['true', '1', 'yes', 'on']
    include_browserconfig = data.get('include_browserconfig', 'true').lower() in ['true', '1', 'yes', 'on']
    include_html = data.get('include_html', 'true').lower() in ['true', '1', 'yes', 'on']
    
    options = batch_data.get('options')
    options_dict = options if isinstance(options, dict) else (options_to_dict(options) if options else {})
    app_name = options_dict.get('app_name', 'icons')
    safe_app_name = ''.join(c for c in app_name if c.isalnum() or c in ('-', '_')).strip() or 'icons'
    
    extra_files = []
    if include_manifest:
        extra_files.append('manifest.json')
    if include_browserconfig:
        extra_files.append('browserconfig.xml')
    if include_html:
        extra_files.append('icons.html')
    
    selected_set = set(selected_files)
    selected_set.update(extra_files)
    output_dirs = batch_data['output_dirs']
    
    zip_buffer = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for original_name, source_dir in output_dirs.items():
            prefix = original_name if len(output_dirs) > 1 else ''
            if not os.path.exists(source_dir):
                continue
            for filename in sorted(os.listdir(source_dir)):
                if filename in selected_set:
                    filepath = os.path.join(source_dir, filename)
                    if os.path.isfile(filepath):
                        arcname = os.path.join(prefix, filename) if prefix else filename
                        zipf.write(filepath, arcname)
    
    zip_buffer.seek(0)
    final_name = custom_name if custom_name else f"{safe_app_name}_icons.zip"
    if not final_name.lower().endswith('.zip'):
        final_name += '.zip'
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=final_name
    )

@main_bp.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413
