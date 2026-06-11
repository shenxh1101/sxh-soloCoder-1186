import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))
    app.config['UPLOAD_FOLDER'] = os.path.abspath(os.getenv('UPLOAD_FOLDER', 'uploads'))
    app.config['OUTPUT_FOLDER'] = os.path.abspath(os.getenv('OUTPUT_FOLDER', 'output'))
    app.config['CACHE_FOLDER'] = os.path.abspath(os.getenv('CACHE_FOLDER', 'cache'))
    
    for folder in ['UPLOAD_FOLDER', 'OUTPUT_FOLDER', 'CACHE_FOLDER']:
        os.makedirs(app.config[folder], exist_ok=True)
    
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
