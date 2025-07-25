from flask import Blueprint, jsonify, current_app, render_template
import os
import mimetypes

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/static-files')
def debug_static_files():
    """Debug endpoint to list all static files and their paths"""
    static_folder = current_app.static_folder
    result = {
        "static_folder": static_folder,
        "exists": os.path.exists(static_folder),
        "files": {}
    }
    
    if os.path.exists(static_folder):
        for root, dirs, files in os.walk(static_folder):
            rel_path = os.path.relpath(root, static_folder)
            if rel_path == '.':
                rel_path = ''
            result["files"][rel_path] = files
    
    return jsonify(result)

@debug_bp.route("/static-info")
def static_info():
    """
    Debug endpoint to check static file paths and availability
    Returns information about static file configuration and example files
    """
    # Get the static folder path
    static_folder = current_app.static_folder
    
    # Check if common static files exist
    test_files = [
        "css/styles.css",
        "js/admin.js",
        "js/charts.js"
    ]
    
    file_info = {}
    for file_path in test_files:
        full_path = os.path.join(static_folder, file_path)
        file_info[file_path] = {
            "exists": os.path.exists(full_path),
            "size": os.path.getsize(full_path) if os.path.exists(full_path) else None,
            "mime_type": mimetypes.guess_type(full_path)[0],
            "absolute_path": full_path
        }
    
    # Get information about the static folder
    try:
        static_files = os.listdir(static_folder)
        static_folders = [d for d in os.listdir(static_folder) if os.path.isdir(os.path.join(static_folder, d))]
    except Exception as e:
        static_files = str(e)
        static_folders = str(e)
    
    result = {
        "app_static_folder": static_folder,
        "static_url_path": current_app.static_url_path,
        "file_info": file_info,
        "static_files_root": static_files[:20] if isinstance(static_files, list) else static_files,
        "static_folders": static_folders,
        "mimetypes_knownfiles": mimetypes.knownfiles,
        "environment": {
            "FLASK_ENV": os.environ.get("FLASK_ENV", "not set"),
            "FLASK_DEBUG": os.environ.get("FLASK_DEBUG", "not set")
        }
    }
    
    return jsonify(result)

@debug_bp.route("/mime-types")
def mime_types():
    """
    Debug endpoint to check MIME type configuration
    """
    common_extensions = [
        ".css", ".js", ".html", ".png", ".jpg", 
        ".svg", ".pdf", ".json", ".txt", ".woff2"
    ]
    
    mime_mapping = {}
    for ext in common_extensions:
        mime_mapping[ext] = mimetypes.types_map.get(ext, "unknown")
    
    # Add some test file paths
    test_paths = [
        "styles.css",
        "admin.js",
        "image.png",
        "document.pdf"
    ]
    
    path_results = {}
    for path in test_paths:
        path_results[path] = mimetypes.guess_type(path)[0]
    
    return jsonify({
        "mime_types_map": mime_mapping,
        "test_paths": path_results,
        "default_encoding": mimetypes.guess_type("test.txt")[1]
    })

@debug_bp.route('/static-test')
def static_test():
    """Debug view to test static file loading"""
    return render_template('debug_static.html')
