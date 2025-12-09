
import os
import time
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from datetime import datetime

# 初始化 Flask 应用
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

def get_env_info():
    """获取环境变量信息"""
    return {
        'RUN_MODE': os.environ.get('RUN_MODE', 'Unknown'),
        'CRON_SCHEDULE': os.environ.get('CRON_SCHEDULE', '未设置'),
        'ENABLE_NOTIFICATION': os.environ.get('ENABLE_NOTIFICATION', 'false'),
        'ENABLE_CRAWLER': os.environ.get('ENABLE_CRAWLER', 'false')
    }

def get_today_file_count():
    """获取今日生成的文件数量"""
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_dir = os.path.join(OUTPUT_DIR, today_str)
        if os.path.exists(today_dir):
            count = 0
            for root, dirs, files in os.walk(today_dir):
                count += len(files)
            return count
        return 0
    except:
        return 0

def get_recent_reports(limit=5):
    """获取最近的报告文件"""
    reports = []
    try:
        # 遍历 output 目录下的日期文件夹
        if os.path.exists(OUTPUT_DIR):
            date_dirs = sorted([d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))], reverse=True)
            
            for date_dir in date_dirs[:2]: # 只看最近两天的
                sub_dir = os.path.join(OUTPUT_DIR, date_dir, 'html')
                if os.path.exists(sub_dir):
                    files = sorted([f for f in os.listdir(sub_dir) if f.endswith('.html')], 
                                   key=lambda x: os.path.getmtime(os.path.join(sub_dir, x)), 
                                   reverse=True)
                    for f in files:
                        full_path = os.path.join(sub_dir, f)
                        rel_path = f"{date_dir}/html/{f}"
                        reports.append({
                            'name': f,
                            'path': rel_path,
                            'time': time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(full_path)))
                        })
                        if len(reports) >= limit:
                            break
                if len(reports) >= limit:
                    break
    except Exception as e:
        print(f"Error getting reports: {e}")
    return reports

@app.route('/')
def index():
    """仪表盘首页"""
    env_info = get_env_info()
    today_files = get_today_file_count()
    recent_reports = get_recent_reports()
    port = request.environ.get('SERVER_PORT')
    
    return render_template('dashboard.html', 
                           env=env_info, 
                           today_files=today_files, 
                           recent_reports=recent_reports,
                           port=port,
                           active_page='dashboard')

@app.route('/config', methods=['GET', 'POST'])
def config():
    """配置管理"""
    filename = request.args.get('file', 'config.yaml')
    if filename not in ['config.yaml', 'frequency_words.txt']:
        filename = 'config.yaml'
        
    file_path = os.path.join(CONFIG_DIR, filename)
    message = None
    
    if request.method == 'POST':
        content = request.form.get('content')
        save_filename = request.form.get('filename')
        
        # 安全检查
        if save_filename in ['config.yaml', 'frequency_words.txt']:
            save_path = os.path.join(CONFIG_DIR, save_filename)
            try:
                # 只是简单的写入，不做YAML校验，防止误报
                with open(save_path, 'w', encoding='utf-8') as f:
                    # 处理换行符，统一使用 \n
                    f.write(content.replace('\r\n', '\n'))
                message = f'{save_filename} 保存成功！'
                filename = save_filename # 保持当前文件
            except Exception as e:
                message = f'保存失败: {str(e)}'
        
    # 读取文件内容
    content = ""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = f"# 文件不存在: {file_path}"
    except Exception as e:
        content = f"# 读取错误: {str(e)}"
        
    return render_template('config.html', 
                           content=content, 
                           current_file=filename, 
                           message=message,
                           active_page='config')

@app.route('/keywords')
def keywords():
    """关键词管理快捷方式"""
    return redirect('/config?file=frequency_words.txt')

@app.route('/history')
def history():
    """历史记录"""
    files_list = []
    try:
        if os.path.exists(OUTPUT_DIR):
            for root, dirs, files in os.walk(OUTPUT_DIR):
                for f in files:
                    if f.endswith('.html') or f.endswith('.txt') or f.endswith('.json'):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, OUTPUT_DIR)
                        stat = os.stat(full_path)
                        
                        files_list.append({
                            'name': f,
                            'path': rel_path,
                            'size': f"{stat.st_size // 1024} KB",
                            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
                            'date': rel_path.split(os.sep)[0] if os.sep in rel_path else 'Unknown',
                            'type': f.split('.')[-1].upper()
                        })
            
            # 按时间倒序
            files_list.sort(key=lambda x: x['time'], reverse=True)
            files_list = files_list[:100] # 只显示最近100条
    except Exception as e:
        print(f"Error getting history: {e}")
        
    return render_template('history.html', files=files_list, active_page='history')

@app.route('/logs')
def logs():
    """日志页面"""
    return render_template('logs.html', active_page='logs')

@app.route('/view/<path:filename>')
def view_file(filename):
    """查看静态文件"""
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/api/run', methods=['POST'])
def run_task():
    """手动执行任务"""
    try:
        # 使用 subprocess 执行 main.py
        # 注意：这里假设 main.py 在当前目录下
        cmd = ["python", "main.py"]
        
        # 增加环境变量标记，避免递归启动web服务器（如果有保护逻辑的话）
        env = os.environ.copy()
        env['NO_WEB_SERVER'] = 'true'
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': '执行成功'})
        else:
            return jsonify({'success': False, 'message': f'执行失败: {result.stderr}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/logs')
def get_logs():
    """获取日志内容"""
    try:
        # 尝试读取 PID 1 的输出，这在 docker 中通常有效
        # 或者尝试读取 docker logs 的替代位置
        log_content = "无法读取日志，请通过 'docker logs trend-radar' 查看。"
        
        # 尝试读取 /tmp/supercronic.log 如果有的话，或者尝试截取 stdout
        # 在容器内部直接读取 stdout 可能受限，这里做个简单模拟或尝试
        
        log_files = ['/proc/1/fd/1', '/tmp/app.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    # 只读取最后 50 行
                    cmd = f"tail -n 50 {log_file}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout:
                        log_content = result.stdout
                        break
                except:
                    continue
                    
        return jsonify({'logs': log_content})
    except Exception as e:
        return jsonify({'logs': f"Error: {str(e)}"})

@app.route('/shutdown')
def shutdown():
    """停止服务"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return 'Not running with the Werkzeug Server'
    func()
    return 'Web Server shutting down...'

def start_server(port=8080):
    """启动 Web 服务器"""
    print(f"🚀 启动 Web 管理界面，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    start_server()
