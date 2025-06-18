from flask import Blueprint, render_template, request, redirect, flash, session, jsonify
import hashlib
import re
from routes.approve_bp import approve_and_store_project # <--- أضف هذا السطر
dept_head_bp = Blueprint('dept_head_bp', __name__)

# قاعدة بيانات رؤساء الأقسام (في التطبيق الحقيقي، ستكون في قاعدة بيانات)
DEPARTMENT_HEADS = {
    'علوم_الحاسوب': {
        'name': 'د. أحمد محمد الصالح',
        'email': 'ahmed.saleh@misuratau.edu.ly',
        'password_hash': hashlib.sha256('cs_head_2025'.encode()).hexdigest(),
        'department': 'علوم_الحاسوب'
    },
    'نظم_الإنترنت': {
        'name': 'د. فاطمة علي النجار',
        'email': 'fatima.najjar@misuratau.edu.ly',
        'password_hash': hashlib.sha256('is_head_2025'.encode()).hexdigest(),
        'department': 'نظم_الإنترنت'
    },
    'الوسائط_المتعددة': {
        'name': 'د. محمد عبدالله الزروق',
        'email': 'mohammed.zarrouk@misuratau.edu.ly',
        'password_hash': hashlib.sha256('mm_head_2025'.encode()).hexdigest(),
        'department': 'الوسائط_المتعددة'
    },
    'أمن_المعلومات': {
        'name': 'د. سارة أحمد المبروك',
        'email': 'sara.mabrouk@misuratau.edu.ly',
        'password_hash': hashlib.sha256('sec_head_2025'.encode()).hexdigest(),
        'department': 'أمن_المعلومات'
    },
    'هندسة_البرمجيات': {
        'name': 'د. عمر محمد الطاهر',
        'email': 'omar.taher@misuratau.edu.ly',
        'password_hash': hashlib.sha256('se_head_2025'.encode()).hexdigest(),
        'department': 'هندسة_البرمجيات'
    },
    'الذكاء_الاصطناعي': {
        'name': 'د. ليلى عبدالرحمن القذافي',
        'email': 'laila.gaddafi@misuratau.edu.ly',
        'password_hash': hashlib.sha256('ai_head_2025'.encode()).hexdigest(),
        'department': 'الذكاء_الاصطناعي'
    }
}

def validate_university_email(email):
    """التحقق من صحة البريد الجامعي"""
    pattern = r'^[a-zA-Z0-9._%+-]+@misuratau\.edu\.ly$'
    return re.match(pattern, email) is not None

def get_department_head_by_email(email):
    """البحث عن رئيس القسم بالبريد الإلكتروني"""
    for dept_key, head_info in DEPARTMENT_HEADS.items():
        if head_info['email'].lower() == email.lower():
            return dept_key, head_info
    return None, None

@dept_head_bp.route('/')
def login_page():
    """صفحة تسجيل دخول رؤساء الأقسام"""
    return render_template('dept_head_login.html')

@dept_head_bp.route('/login', methods=['GET', 'POST'])
def login():
    """معالجة تسجيل الدخول"""
    if request.method == 'GET':
        return render_template('dept_head_login.html')
    
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    # التحقق من صحة البيانات
    if not email or not password:
        flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'error')
        return render_template('dept_head_login.html')
    
    # التحقق من صحة البريد الجامعي
    if not validate_university_email(email):
        flash('يرجى استخدام البريد الإلكتروني الجامعي (@misuratau.edu.ly)', 'error')
        return render_template('dept_head_login.html')
    
    # البحث عن رئيس القسم
    dept_key, head_info = get_department_head_by_email(email)
    
    if not head_info:
        flash('البريد الإلكتروني غير مسجل كرئيس قسم', 'error')
        return render_template('dept_head_login.html')
    
    # التحقق من كلمة المرور
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != head_info['password_hash']:
        flash('كلمة المرور غير صحيحة', 'error')
        return render_template('dept_head_login.html')
    
    # تسجيل الدخول بنجاح
    session['dept_head_logged_in'] = True
    session['dept_head_email'] = email
    session['dept_head_name'] = head_info['name']
    session['dept_head_department'] = head_info['department']
    session['dept_head_key'] = dept_key
    
    flash(f'مرحباً {head_info["name"]} - رئيس قسم {head_info["department"]}', 'success')
    return redirect('/dept-head/dashboard')

@dept_head_bp.route('/dashboard')
def dashboard():
    """لوحة تحكم رئيس القسم"""
    if not session.get('dept_head_logged_in'):
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect('/dept-head/login')
    
    # جلب المشاريع الخاصة بالقسم
    department = session.get('dept_head_department')
    dept_projects = get_department_projects(department)
    pending_projects = get_pending_department_projects(department)
    
    return render_template('dept_head_dashboard.html', 
                         projects=dept_projects,
                         pending_projects=pending_projects,
                         department=department,
                         head_name=session.get('dept_head_name'))

@dept_head_bp.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect('/dept-head/login')

@dept_head_bp.route('/approve-department-project', methods=['POST'])
def approve_department_project():
    """اعتماد مشروع من قبل رئيس القسم وحفظه مباشرة في قاعدة البيانات"""
    if not session.get('dept_head_logged_in'):
        return jsonify({'success': False, 'message': 'غير مخول'}), 401

    try:
        data = request.get_json()
        project_index = data.get('project_index')
        action = data.get('action')
        comments = data.get('comments', '')

        # استيراد قائمة المشاريع المعلقة
        from routes.submit_bp import pending_projects

        if project_index is None or not (0 <= project_index < len(pending_projects)):
            return jsonify({'success': False, 'message': 'مشروع غير موجود أو فهرس خاطئ'}), 400

        project = pending_projects[project_index]
        department = session.get('dept_head_department')

        if project.get('department') != department:
            return jsonify({'success': False, 'message': 'غير مخول لاعتماد هذا المشروع'}), 403

        if action == 'approve':
            # --- التعديل الأساسي هنا ---
            # الآن سنقوم باستدعاء دالة الحفظ النهائية مباشرة
            project['dept_head_comments'] = comments # حفظ تعليق رئيس القسم
            success = approve_and_store_project(project)

            if success:
                # إذا نجح الحفظ، قم بإزالة المشروع من قائمة الانتظار
                pending_projects.pop(project_index)
                return jsonify({
                    'success': True, 
                    'message': 'تم اعتماد المشروع وحفظه في قاعدة البيانات بنجاح.'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'حدث خطأ أثناء حفظ المشروع في قاعدة البيانات.'
                }), 500

        elif action == 'reject':
            # منطق الرفض يبقى كما هو
            pending_projects.pop(project_index)
            return jsonify({
                'success': True, 
                'message': 'تم رفض المشروع من قبل رئيس القسم'
            })

        else:
            return jsonify({'success': False, 'message': 'إجراء غير صحيح'}), 400

    except Exception as e:
        print(f"خطأ في معالجة طلب رئيس القسم: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في الخادم'}), 500
def get_department_projects(department):
    """جلب مشاريع القسم من قاعدة البيانات"""
    try:
        import requests
        
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?student ?supervisor ?year ?abstract
        WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:hasEnrolledStudent ?studentEntity ;
                     gpo:isSupervisedBySupervisor ?supervisorEntity ;
                     gpo:belongsToDepartment ?departmentEntity ;
                     gpo:hasAcademicYear ?year ;
                     gpo:hasAbstract ?abstract .
            
            ?studentEntity gpo:hasName ?student .
            ?supervisorEntity gpo:hasName ?supervisor .
            ?departmentEntity gpo:hasName ?department .
            
            FILTER (LCASE(STR(?department)) = LCASE("{department}"))
        }}
        ORDER BY DESC(?year) ?title
        '''
        
        response = requests.post(
            'http://localhost:3030/graduation/sparql',
            data={'query': sparql_query},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=30
        )
        
        projects = []
        if response.ok:
            data = response.json()
            if 'results' in data and 'bindings' in data['results']:
                for row in data['results']['bindings']:
                    project = {}
                    for key, value in row.items():
                        project[key] = value.get('value', '')
                    projects.append(project)
        
        return projects
        
    except Exception as e:
        print(f"خطأ في جلب مشاريع القسم: {e}")
        return []

def get_pending_department_projects(department):
    """جلب المشاريع المعلقة للقسم"""
    from routes.submit_bp import pending_projects
    
    dept_pending = []
    for i, project in enumerate(pending_projects):
        if project.get('department') == department:
            project['index'] = i  # إضافة الفهرس للاستخدام في الاعتماد
            dept_pending.append(project)
    
    return dept_pending

