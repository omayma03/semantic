# الملف: routes/approve_bp.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect
import requests
from logic.rdf_generator import create_project_rdf
import os 
approve_bp = Blueprint('approve_bp', __name__)

# استيراد قائمة المشاريع المعلقة من submit_bp
from routes.submit_bp import pending_projects

@approve_bp.route('/')
def view_pending_projects():
    """عرض المشاريع المعلقة للاعتماد"""
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
        action = data.get('action')
        reason = data.get('reason', '')
        
        # استخدام نسخة من القائمة لتجنب مشاكل التزامن
        current_pending_projects = list(pending_projects)

        if project_index is None or not (0 <= project_index < len(current_pending_projects)):
            return jsonify({'success': False, 'message': 'مشروع غير موجود أو فهرس خاطئ'}), 400
        
        project = current_pending_projects[project_index]
        
        if action == 'approve':
            success = approve_and_store_project(project)
            if success:
                # إزالة المشروع من القائمة الأصلية
                pending_projects.pop(project_index)
                return jsonify({'success': True, 'message': 'تم اعتماد المشروع وحفظه بنجاح'})
            else:
                return jsonify({'success': False, 'message': 'فشل في حفظ المشروع'}), 500
                
        elif action == 'reject':
            project['status'] = 'rejected'
            project['rejection_reason'] = reason
            pending_projects.pop(project_index)
            return jsonify({'success': True, 'message': f'تم رفض المشروع. السبب: {reason}'})
        
        else:
            return jsonify({'success': False, 'message': 'إجراء غير صحيح'}), 400
            
    except Exception as e:
        print(f"خطأ في معالجة طلب الاعتماد: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في الخادم'}), 500



def approve_and_store_project(project):
    """اعتماد المشروع، حفظه بشكل دائم في الملف، ثم إرساله إلى Fuseki"""
    try:
        project['status'] = 'approved'
        rdf_data = create_project_rdf(project)
        
        # --- الحل النهائي باستخدام المسار الصحيح ---
        
        # الحصول على المسار الجذر للمشروع
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # >> التعديل هنا ليطابق مجلدك <<
        # استخدام مجلد 'ontology' بدلاً من 'data'
        ontology_file_path = os.path.join(project_root, 'ontology', 'projects_converted.ttl')
        
        try:
            with open(ontology_file_path, 'a', encoding='utf-8') as f:
                f.write('\n\n' + rdf_data)
            print(f"تمت كتابة المشروع '{project['title']}' بنجاح إلى الملف الدائم: {ontology_file_path}")
        except Exception as file_error:
            print(f"فشل في الكتابة إلى ملف الأنطولوجيا: {file_error}")
            return False

        # --- إرسال البيانات إلى خادم Fuseki الذي يعمل حاليًا ---
        headers = {'Content-Type': 'text/turtle'}
        response = requests.post(
            'http://localhost:3030/graduation/data?default',
            data=rdf_data.encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        if response.ok:
            print(f"تم إرسال المشروع '{project['title']}' بنجاح إلى Fuseki.")
            return True
        else:
            print(f"فشل في إرسال البيانات إلى Fuseki: {response.status_code} - {response.text}")
            return True
            
    except Exception as e:
        print(f"خطأ في اعتماد المشروع: {e}")
        return False

@approve_bp.route('/approved-projects')
def view_approved_projects():
    """عرض المشاريع المعتمدة من قاعدة البيانات"""
    try:
        # --- إصلاح: تم تصحيح استعلام SPARQL ليطابق هيكل بياناتك ---
        sparql_query = '''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?department ?year ?abstract 
                        (GROUP_CONCAT(DISTINCT ?studentName; separator=", ") AS ?students)
                        ?supervisorName
        WHERE {
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:hasAcademicYear ?year .

            OPTIONAL {
                ?project gpo:belongsToDepartment ?deptEntity .
                BIND(REPLACE(STRAFTER(STR(?deptEntity), "Department_"), "_", " ") AS ?department)
            }
            OPTIONAL { ?project gpo:hasAbstract ?abstract . }
            OPTIONAL {
                ?project gpo:hasEnrolledStudent ?studentEntity .
                ?studentEntity gpo:studentName ?studentName .
            }
            OPTIONAL {
                ?project gpo:isSupervisedBySupervisor ?supervisorEntity .
                ?supervisorEntity gpo:supervisorName ?supervisorName .
            }
        }
        GROUP BY ?project ?title ?department ?year ?abstract ?supervisorName
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
                    approved_projects.append({
                        'title': row.get('title', {}).get('value', 'غير محدد'),
                        'department': row.get('department', {}).get('value', 'غير محدد'),
                        'year': row.get('year', {}).get('value', 'غير محدد'),
                        'abstract': row.get('abstract', {}).get('value', 'غير متوفر'),
                        'students': row.get('students', {}).get('value', 'غير محدد'),
                        'supervisor': row.get('supervisorName', {}).get('value', 'غير محدد')
                    })
        
        return render_template('approved_projects.html', projects=approved_projects)
        
    except Exception as e:
        print(f"خطأ في جلب المشاريع المعتمدة: {e}")
        flash('حدث خطأ في جلب المشاريع المعتمدة', 'error')
        return render_template('approved_projects.html', projects=[])

@approve_bp.route('/project-statistics')
def project_statistics():
    """إحصائيات المشاريع"""
    try:
        # --- إصلاح: تم تصحيح استعلام SPARQL لجلب إحصائيات الأقسام بشكل صحيح ---
        stats_query = '''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT ?department (COUNT(?project) as ?count)
        WHERE {
            ?project a gpo:Project ;
                     gpo:belongsToDepartment ?departmentEntity .
            BIND(REPLACE(STRAFTER(STR(?departmentEntity), "Department_"), "_", " ") AS ?department)
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