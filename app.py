import os
import sys
import logging

# Disable Numba JIT to prevent caching errors in serverless environment
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['NUMBA_CACHE_DIR'] = '/tmp'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template, request, jsonify, send_file
    from routes.api_routes import api_bp
    # stock_mapping import might fail if paths are wrong
    from stock_mapping import add_stock_suffix
except Exception as e:
    logger.error(f"Import Error: {e}")
    # Create a dummy app to show error
    app = Flask(__name__)
    @app.route('/')
    def error_page():
        return f"Startup Error: {e}", 500
    raise e

# Disable Werkzeug logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Register API Blueprint
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    """Home Page"""
    return render_template('index.html')

@app.route('/batch_analysis')
def batch_analysis():
    """Batch Analysis Page"""
    return render_template('batch_analysis.html')

@app.route('/batch_results')
def batch_results():
    """Batch Results Page"""
    return render_template('batch_results.html')

@app.route('/backtest')
def backtest_page():
    """Offline Backtest Page"""
    return render_template('backtest.html')

@app.route('/correlation_analysis')
def correlation_analysis_page():
    """Correlation Analysis Page"""
    return render_template('correlation_analysis.html')

@app.route('/info_collection')
def info_collection_page():
    """Info Collection Page"""
    return render_template('info_collection.html')

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)