import requests
from urllib.parse import quote

class DuplicateChecker:
    """فئة للتحقق من تكرار المشاريع باستخدام استعلامات SPARQL"""
    
    def __init__(self, fuseki_url="http://localhost:3030/graduation/sparql"):
        self.fuseki_url = fuseki_url
    
    def check_duplicate_project(self, title, supervisor, students):
        """
        التحقق من وجود مشروع مكرر بناءً على العنوان والمشرف والطلاب
        
        Args:
            title (str): عنوان المشروع
            supervisor (str): اسم المشرف
            students (list): قائمة بأسماء الطلاب
            
        Returns:
            dict: نتيجة التحقق تحتوي على معلومات التكرار
        """
        
        # تنظيف البيانات المدخلة
        title = title.strip()
        supervisor = supervisor.strip()
        students = [s.strip() for s in students if s.strip()]
        
        # التحقق من تكرار العنوان
        title_duplicates = self._check_title_duplicate(title)
        
        # التحقق من تكرار المشرف مع نفس العنوان
        supervisor_duplicates = self._check_supervisor_duplicate(title, supervisor)
        
        # التحقق من تكرار الطلاب
        student_duplicates = self._check_student_duplicates(students)
        
        # تحليل النتائج
        result = {
            'is_duplicate': False,
            'duplicate_type': None,
            'duplicate_details': {},
            'warnings': [],
            'existing_projects': []
        }
        
        # تحديد نوع التكرار
        if title_duplicates:
            result['is_duplicate'] = True
            result['duplicate_type'] = 'title_match'
            result['duplicate_details'] = {
                'message': 'يوجد مشروع بنفس العنوان أو عنوان مشابه جداً.',
                'existing_projects': title_duplicates
            }
        
        if supervisor_duplicates and not result['is_duplicate']:
            result['is_duplicate'] = True
            result['duplicate_type'] = 'supervisor_title_match'
            result['duplicate_details'] = {
                'message': 'يوجد مشروع لنفس المشرف بنفس العنوان.',
                'existing_projects': supervisor_duplicates
            }

        if student_duplicates and not result['is_duplicate']:
            result['is_duplicate'] = True
            result['duplicate_type'] = 'student_project_exists'
            result['duplicate_details'] = {
                'message': 'أحد الطلاب لديه مشروع آخر مسجل.',
                'existing_projects': student_duplicates
            }

        # إذا لم يكن هناك تكرار مباشر، تحقق من التحذيرات
        if not result['is_duplicate']:
            if title_duplicates:
                result['warnings'].append({
                    'type': 'similar_title',
                    'message': 'يوجد مشروع بعنوان مشابه.',
                    'existing_projects': title_duplicates
                })
            if supervisor_duplicates:
                result['warnings'].append({
                    'type': 'similar_supervisor_title',
                    'message': 'يوجد مشروع آخر لنفس المشرف بعنوان مشابه.',
                    'existing_projects': supervisor_duplicates
                })
            if student_duplicates:
                result['warnings'].append({
                    'type': 'student_already_has_project',
                    'message': 'أحد الطلاب لديه مشروع آخر مسجل.',
                    'existing_projects': student_duplicates
                })
        
        return result
    
    def _check_title_duplicate(self, title):
        """التحقق من تكرار العنوان"""
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?supervisorName ?year
        WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:isSupervisedBySupervisor ?supervisorEntity ;
                     gpo:hasAcademicYear ?year .
            
            ?supervisorEntity gpo:hasName ?supervisorName .
            
            FILTER (
                REGEX(LCASE(STR(?title)), LCASE("{self._escape_sparql_string(title)}"), "i") ||
                LCASE(STR(?title)) = LCASE("{self._escape_sparql_string(title)}")
            )
        }}
        '''
        
        return self._execute_sparql_query(sparql_query)
    
    def _check_supervisor_duplicate(self, title, supervisor):
        """التحقق من تكرار المشرف مع نفس العنوان"""
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?supervisorName ?year
        WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:isSupervisedBySupervisor ?supervisorEntity ;
                     gpo:hasAcademicYear ?year .
            
            ?supervisorEntity gpo:hasName ?supervisorName .
            
            FILTER (
                (REGEX(LCASE(STR(?title)), LCASE("{self._escape_sparql_string(title)}"), "i") || LCASE(STR(?title)) = LCASE("{self._escape_sparql_string(title)}")) &&
                REGEX(LCASE(STR(?supervisorName)), LCASE("{self._escape_sparql_string(supervisor)}"), "i")
            )
        }}
        '''
        
        return self._execute_sparql_query(sparql_query)
    
    def _check_student_duplicates(self, students):
        """التحقق من تكرار الطلاب"""
        if not students:
            return []
        
        # بناء فلتر للطلاب
        student_filters = []
        for student in students:
            student_filters.append(f'REGEX(LCASE(STR(?studentName)), LCASE("{self._escape_sparql_string(student)}"), "i")')
        
        student_filter = ' || '.join(student_filters)
        
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?studentName ?supervisorName ?year
        WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:hasEnrolledStudent ?studentEntity ;
                     gpo:isSupervisedBySupervisor ?supervisorEntity ;
                     gpo:hasAcademicYear ?year .
            
            ?studentEntity gpo:hasName ?studentName .
            ?supervisorEntity gpo:hasName ?supervisorName .
            
            FILTER ({student_filter})
        }}
        '''
        
        return self._execute_sparql_query(sparql_query)
    
    def _execute_sparql_query(self, query):
        """تنفيذ استعلام SPARQL وإرجاع النتائج"""
        print(f"\n--- SPARQL Query ---\n{query}\n--------------------\n") # Debug print
        try:
            response = requests.post(
                self.fuseki_url,
                data={'query': query},
                headers={'Accept': 'application/sparql-results+json'},
                timeout=30
            )
            
            print(f"--- SPARQL Response Status: {response.status_code} ---\n") # Debug print
            print(f"--- SPARQL Response Text: {response.text} ---\n") # Debug print

            if response.ok:
                data = response.json()
                results = []
                
                if 'results' in data and 'bindings' in data['results']:
                    for row in data['results']['bindings']:
                        result = {}
                        for key, value in row.items():
                            result[key] = value.get('value', '')
                        results.append(result)
                
                print(f"--- SPARQL Results: {results} ---\n") # Debug print
                return results
            else:
                print(f"SPARQL query failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error executing SPARQL query: {e}")
            return []
    
    def _escape_sparql_string(self, text):
        """تنظيف النص لاستخدامه في استعلامات SPARQL"""
        if not text:
            return ""
        
        # إزالة الأحرف الخاصة التي قد تسبب مشاكل في SPARQL
        text = text.replace('"', '\"')
        text = text.replace('\\', '\\\\')
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        
        return text
    
    def get_duplicate_summary(self, check_result):
        """إنشاء ملخص مفصل عن نتائج التحقق من التكرار"""
        summary = {
            'status': 'approved' if not check_result['is_duplicate'] else 'rejected',
            'message': '',
            'details': [],
            'recommendations': []
        }
        
        if check_result['is_duplicate']:
            summary['message'] = 'تم رفض المشروع بسبب التكرار'
            summary['details'].append(check_result['duplicate_details']['message'])
            for proj in check_result['duplicate_details']['existing_projects']:
                summary['details'].append(f"  - المشروع: {proj.get('title', 'غير معروف')}، المشرف: {proj.get('supervisorName', 'غير معروف')}، السنة: {proj.get('year', 'غير معروف')}")
            summary['recommendations'].append('يرجى مراجعة تفاصيل المشروع والتأكد من عدم تكراره.')
        else:
            summary['message'] = 'تم قبول المشروع'
            
            if check_result['warnings']:
                summary['message'] += ' مع تحذيرات'
                for warning in check_result['warnings']:
                    summary['details'].append(warning['message'])
                    if 'existing_projects' in warning:
                        for proj in warning['existing_projects']:
                            summary['details'].append(f"  - المشروع: {proj.get('title', 'غير معروف')}، المشرف: {proj.get('supervisorName', 'غير معروف')}، السنة: {proj.get('year', 'غير معروف')}")
                    
                    if warning['type'] == 'similar_title':
                        summary['recommendations'].append('تأكد من أن مشروعك مختلف عن المشاريع المشابهة.')
                    elif warning['type'] == 'student_already_has_project':
                        summary['recommendations'].append('تأكد من أن الطالب لا يشارك في مشروع آخر.')
                    elif warning['type'] == 'similar_supervisor_title':
                        summary['recommendations'].append('تأكد من أن مشروعك مختلف عن المشاريع المشابهة لنفس المشرف.')
        
        return summary


