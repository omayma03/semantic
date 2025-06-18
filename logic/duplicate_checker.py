import requests
from urllib.parse import quote

class DuplicateChecker:
    """فئة للتحقق من تكرار المشاريع باستخدام استعلامات SPARQL"""
    
    def __init__(self, fuseki_url="http://localhost:3030/graduation/sparql"):
        self.fuseki_url = fuseki_url
    
    def check_duplicate_project(self, title, supervisor, students):
        title = title.strip()
        supervisor = supervisor.strip()
        students = [s.strip() for s in students if s.strip()]
        
        title_duplicates = self._check_title_duplicate(title)
        if title_duplicates:
            return {'is_duplicate': True, 'duplicate_details': {'message': 'يوجد مشروع بنفس العنوان.', 'existing_projects': title_duplicates}}

        supervisor_duplicates = self._check_supervisor_duplicate(title, supervisor)
        if supervisor_duplicates:
            return {'is_duplicate': True, 'duplicate_details': {'message': 'يوجد مشروع لنفس المشرف وبنفس العنوان.', 'existing_projects': supervisor_duplicates}}

        student_duplicates = self._check_student_duplicates(students)
        if student_duplicates:
            return {'is_duplicate': True, 'duplicate_details': {'message': 'أحد الطلاب لديه مشروع آخر مسجل.', 'existing_projects': student_duplicates}}
            
        return {'is_duplicate': False}
    
    def _check_title_duplicate(self, title):
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        SELECT ?title WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title .
            FILTER (REGEX(LCASE(STR(?title)), LCASE("{self._escape_sparql_string(title)}"), "i"))
        }} LIMIT 1
        '''
        return self._execute_sparql_query(sparql_query)
    
    def _check_supervisor_duplicate(self, title, supervisor):
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        SELECT ?title ?supervisorName WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:isSupervisedBySupervisor ?supervisorEntity .
            ?supervisorEntity gpo:supervisorName ?supervisorName .
            FILTER (
                REGEX(LCASE(STR(?title)), LCASE("{self._escape_sparql_string(title)}"), "i") &&
                REGEX(LCASE(STR(?supervisorName)), LCASE("{self._escape_sparql_string(supervisor)}"), "i")
            )
        }} LIMIT 1
        '''
        return self._execute_sparql_query(sparql_query)
    
    def _check_student_duplicates(self, students):
        if not students:
            return []
        
        student_filters = ' || '.join([
            f'REGEX(LCASE(STR(?studentName)), LCASE("{self._escape_sparql_string(student)}"), "i")'
            for student in students
        ])
        
        sparql_query = f'''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        SELECT ?title ?studentName WHERE {{
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:hasEnrolledStudent ?studentEntity .
            ?studentEntity gpo:studentName ?studentName .
            FILTER ({student_filters})
        }}
        '''
        return self._execute_sparql_query(sparql_query)
    
    def _execute_sparql_query(self, query):
        try:
            response = requests.get(
                self.fuseki_url,
                params={'query': query},
                headers={'Accept': 'application/sparql-results+json'},
                timeout=30
            )
            if response.ok:
                return response.json().get('results', {}).get('bindings', [])
            else:
                return []
        except requests.exceptions.RequestException:
            return []
            
    def _escape_sparql_string(self, text):
        if not text: return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')

    def get_duplicate_summary(self, check_result):
        # هذه الدالة أصبحت أبسط الآن
        if not check_result.get('is_duplicate'):
            return {'message': 'لم يتم العثور على تكرار.'}
        
        details = check_result.get('duplicate_details', {})
        message = details.get('message', 'تم اكتشاف تكرار.')
        return {'message': message, 'details': details.get('existing_projects', [])}