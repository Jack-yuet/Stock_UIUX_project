from flask import Flask, render_template, request, jsonify, send_file
from routes.api_routes import api_bp
from stock_mapping import add_stock_suffix
import os
import logging

# 禁用Flask的HTTP请求日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# 注册API蓝图
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/batch_analysis')
def batch_analysis():
    """批量分析页面"""
    return render_template('batch_analysis.html')

@app.route('/batch_results')
def batch_results():
    """批量分析结果页面"""
    return render_template('batch_results.html')

@app.route('/backtest')
def backtest_page():
    """离线回测与模型页面"""
    return render_template('backtest.html')

@app.route('/correlation_analysis')
def correlation_analysis_page():
    """美股A股相关性分析页面"""
    return render_template('correlation_analysis.html')

@app.route('/info_collection')
def info_collection_page():
    """股票信息收集页面"""
    return render_template('info_collection.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)