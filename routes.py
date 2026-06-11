import os
import io
import uuid
import tempfile
import json
from flask import Blueprint, render_template, request, jsonify, send_file, abort, current_app, url_for, send_from_directory
from werkzeug.utils import secure_filename

from utils import (
    allowed_file, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_EXTENSIONS,
    get_file_hash, save_uploaded_file, extract_zip, parse_size_str
)
from icon_generator import ProcessingOptions
from icon_service import generate_icon_set
from cache import CacheManager
from zip_exporter import create_zip_from_directory, create_zip_from_multiple_directories

main_bp = Blueprint('main', __name__)

def get_cache_manager():
    if not hasattr(current_app, 'cache_manager'):
        current_app.cache_manager = CacheManager(current_app.config['CACHE_FOLDER'])
    return current_app.cache_manager

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
    
    custom_filenames = {}
    filenames_input = form.get('custom_filenames', '').strip()
    if filenames_input:
        try:
            custom_filenames = json.loads(filenames_input)
        except:
            pass
    
    app_name = form.get('app_name', 'My App').strip() or 'My App'
    app_short_name = form.get('app_short_name', 'App').strip() or 'App'
    theme_color = form.get('theme_color', '#ffffff').strip() or '#ffffff'
    background_color_manifest = form.get('background_color_manifest', '#ffffff').strip() or '#ffffff'
    
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
        background_color_manifest=background_color_manifest
    )

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    options = parse_options_from_request(request)
    cache_mgr = get_cache_manager()
    
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
    
    results = []
    temp_output_dirs = {}
    
    for image_path in image_paths:
        try:
            with open(image_path, 'rb') as f:
                file_content = f.read()
            file_hash = get_file_hash(file_content)
            cache_key = cache_mgr.get_cache_key(file_hash, options)
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
                continue
            
            output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], str(uuid.uuid4()))
            os.makedirs(output_dir, exist_ok=True)
            
            generated_files = generate_icon_set(image_path, options, output_dir)
            
            cache_mgr.set(cache_key, generated_files, output_dir, original_name)
            
            result_data = {
                'original_name': original_name,
                'file_hash': file_hash,
                'cache_key': cache_key,
                'cached': False,
                'files': {k: {
                    'filename': v['filename'],
                    'type': v.get('type', ''),
                    'size': v.get('size'),
                    'sizes': v.get('sizes')
                } for k, v in generated_files.items() if 'filename' in v},
                'cache_dir': output_dir
            }
            results.append(result_data)
            temp_output_dirs[original_name] = output_dir
            
        except Exception as e:
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
    
    batch_id = str(uuid.uuid4())
    current_app.config.setdefault('BATCH_RESULTS', {})
    current_app.config['BATCH_RESULTS'][batch_id] = {
        'results': results,
        'output_dirs': temp_output_dirs,
        'options': options
    }
    
    return jsonify({
        'success': True,
        'batch_id': batch_id,
        'count': len(results),
        'is_batch': is_batch,
        'results': results
    })

@main_bp.route('/preview/<batch_id>')
def preview(batch_id):
    batch_results = current_app.config.get('BATCH_RESULTS', {}).get(batch_id)
    if not batch_results:
        abort(404)
    
    return render_template('preview.html', 
                           batch_id=batch_id, 
                           results=batch_results['results'],
                           is_batch=len(batch_results['results']) > 1)

@main_bp.route('/preview/file/<batch_id>/<original_name>/<filename>')
def preview_file(batch_id, original_name, filename):
    batch_results = current_app.config.get('BATCH_RESULTS', {}).get(batch_id)
    if not batch_results:
        abort(404)
    
    output_dir = batch_results['output_dirs'].get(original_name)
    if not output_dir:
        abort(404)
    
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        abort(404)
    
    return send_from_directory(output_dir, filename)

@main_bp.route('/download/<batch_id>')
def download(batch_id):
    batch_results = current_app.config.get('BATCH_RESULTS', {}).get(batch_id)
    if not batch_results:
        abort(404)
    
    output_dirs = batch_results['output_dirs']
    
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
    batch_results = current_app.config.get('BATCH_RESULTS', {}).get(batch_id)
    if not batch_results:
        abort(404)
    
    output_dir = batch_results['output_dirs'].get(original_name)
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

@main_bp.route('/api/cache/stats')
def cache_stats():
    cache_mgr = get_cache_manager()
    stats = cache_mgr.get_stats()
    return jsonify(stats)

@main_bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    cache_mgr = get_cache_manager()
    cache_mgr.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'})

@main_bp.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413
