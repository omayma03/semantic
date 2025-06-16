from flask import Blueprint, render_template, request, jsonify, flash, redirect
import requests
from logic.rdf_generator import create_project_rdf

approve_bp = Blueprint('approve_bp', __name__)

# استيراد قائمة المشاريع المعلقة من submit_bp
from routes.submit_bp import pending_projects

@approve_bp.route('/')
def view_pending_projects():
    """عرض المشاريع المعلقة للاعتماد"""
    # فلترة المشاريع المعتمدة من رؤساء الأقسام أو المشاريع المعلقة
    approved_by_dept_head = [p for p in pending_projects if p.get('status') == 'approved_by_dept_head']
    regular_pending = [p for p in pending_projects if p.get('status') != 'approved_by_dept_head' and p.get('status') != 'rejected_by_dept_head']
    
    all_pending = approved_by_dept_head + regular_pending
    
    return render_template('approve_projects.html', projects=all_pending)

@approve_bp.route('/approve-project', methods=['POST'])
def approve_project():
    """اعتماد أو رفض مشروع"""
    try:
        data = request.get_json()
        project_index = data.get('project_index')
        action = data.get('action')  # 'approve' أو 'reject'
        reason = data.get('reason', '')  # سبب الرفض إذا كان الإجراء رفض
        
        if project_index is None or project_index >= len(pending_projects):
            return jsonify({'success': False, 'message': 'مشروع غير موجود'}), 400
        
        project = pending_projects[project_index]
        
        if action == 'approve':
            # اعتماد المشروع - إرسال البيانات إلى Fuseki
            success = approve_and_store_project(project)
            if success:
                # إزالة المشروع من قائمة المعلقة
                pending_projects.pop(project_index)
                return jsonify({
                    'success': True, 
                    'message': 'تم اعتماد المشروع وإضافته إلى قاعدة البيانات'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'فشل في إضافة المشروع إلى قاعدة البيانات'
                }), 500
                
        elif action == 'reject':
            # رفض المشروع
            project['status'] = 'rejected'
            project['rejection_reason'] = reason
            
            # إزالة المشروع من قائمة المعلقة (أو يمكن نقله إلى قائمة منفصلة للمرفوضة)
            pending_projects.pop(project_index)
            
            return jsonify({
                'success': True, 
                'message': f'تم رفض المشروع. السبب: {reason}'
            })
        
        else:
            return jsonify({'success': False, 'message': 'إجراء غير صحيح'}), 400
            
    except Exception as e:
        print(f"خطأ في معالجة طلب الاعتماد: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في الخادم'}), 500

def approve_and_store_project(project):
    """اعتماد المشروع وإضافته إلى Fuseki"""
    try:
        # تحديث حالة المشروع
        project['status'] = 'approved'
        
        # إنشاء RDF للمشروع المعتمد
        rdf_data = create_project_rdf(project)
        
        # إرسال البيانات إلى Fuseki
        headers = {'Content-Type': 'text/turtle'}
        response = requests.post(
            'http://localhost:3030/graduation/data',
            data=rdf_data.encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        if response.ok:
            print(f"تم اعتماد المشروع بنجاح: {project['title']}")
            return True
        else:
            print(f"فشل في إرسال البيانات إلى Fuseki: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"خطأ في اعتماد المشروع: {e}")
        return False

@approve_bp.route('/approved-projects')
def view_approved_projects():
    """عرض المشاريع المعتمدة من قاعدة البيانات"""
    try:
        # استعلام SPARQL لجلب المشاريع المعتمدة
        sparql_query = '''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?student ?supervisor ?department ?year ?abstract
        WHERE {
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
            
            OPTIONAL { ?project gpo:hasStatus ?status }
            FILTER (!BOUND(?status) || ?status = "approved")
        }
        ORDER BY DESC(?year) ?title
        '''
        
        response = requests.post(
            'http://localhost:3030/graduation/sparql',
            data={'query': sparql_query},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=30
        )
        
        approved_projects = []
        if response.ok:
            data = response.json()
            if 'results' in data and 'bindings' in data['results']:
                for row in data['results']['bindings']:
                    project = {}
                    for key, value in row.items():
                        project[key] = value.get('value', '')
                    approved_projects.append(project)
        
        return render_template('approved_projects.html', projects=approved_projects)
        
    except Exception as e:
        print(f"خطأ في جلب المشاريع المعتمدة: {e}")
        flash('حدث خطأ في جلب المشاريع المعتمدة', 'error')
        return render_template('approved_projects.html', projects=[])

@approve_bp.route('/project-statistics')
def project_statistics():
    """إحصائيات المشاريع"""
    try:
        # استعلام لجلب إحصائيات المشاريع
        stats_query = '''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT ?department (COUNT(?project) as ?count)
        WHERE {
            ?project a gpo:Project ;
                     gpo:belongsToDepartment ?departmentEntity .
            ?departmentEntity gpo:hasName ?department .
        }
        GROUP BY ?department
        ORDER BY DESC(?count)
        '''
        
        response = requests.post(
            'http://localhost:3030/graduation/sparql',
            data={'query': stats_query},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=30
        )
        
        statistics = {
            'total_pending': len(pending_projects),
            'department_stats': [],
            'total_approved': 0
        }
        
        if response.ok:
            data = response.json()
            if 'results' in data and 'bindings' in data['results']:
                for row in data['results']['bindings']:
                    dept_stat = {
                        'department': row['department']['value'],
                        'count': int(row['count']['value'])
                    }
                    statistics['department_stats'].append(dept_stat)
                    statistics['total_approved'] += dept_stat['count']
        
        return jsonify(statistics)
        
    except Exception as e:
        print(f"خطأ في جلب الإحصائيات: {e}")
        return jsonify({'error': 'حدث خطأ في جلب الإحصائيات'}), 500

