from flask import Flask
from routes.home_bp import home_bp
from routes.submit_bp import submit_bp
from routes.approve_bp import approve_bp
from routes.search_bp import search_bp
from routes.dept_head_bp import dept_head_bp

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'graduation@portal_2025_enhanced'

# تسجيل جميع المسارات
app.register_blueprint(home_bp)
app.register_blueprint(submit_bp, url_prefix="/submit")
app.register_blueprint(approve_bp, url_prefix="/approve")
app.register_blueprint(search_bp, url_prefix="/search")
app.register_blueprint(dept_head_bp, url_prefix="/dept-head")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

