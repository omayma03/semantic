# الملف: routes/search_bp.py

from flask import Blueprint, render_template, request, jsonify
import requests
import re

search_bp = Blueprint('search_bp', __name__)

class SmartSearchEngine:
    """محرك بحث ذكي يفهم السياق والعلاقات في النص الحر"""
    
    def __init__(self):
        self.keywords_map = {
            'علوم_الحاسوب': ['علوم الحاسوب', 'حاسوب', 'كمبيوتر', 'computer science', 'cs'],
            'نظم_الإنترنت': ['نظم الإنترنت', 'انترنت', 'شبكات', 'internet systems', 'networks'],
            'الوسائط_المتعددة': ['وسائط متعددة', 'ملتيميديا', 'multimedia', 'وسائط'],
            'هندسة_البرمجيات': ['هندسة البرمجيات', 'software engineering', 'se'],
            'نظم_المعلومات': ['نظم المعلومات', 'information systems', 'is'],
            'الشبكات_والاتصالات': ['الشبكات والاتصالات', 'telecommunications'],
            'ذكاء_اصطناعي': ['ذكاء اصطناعي', 'ai', 'artificial intelligence', 'machine learning', 'تعلم آلي'],
            'أمن_معلومات': ['أمن', 'حماية', 'security', 'cybersecurity', 'أمان', 'sql injection', 'xss'],
            'قواعد_بيانات': ['قاعدة بيانات', 'database', 'sql', 'بيانات'],
            'تطبيقات_موبايل': ['موبايل', 'هاتف', 'mobile', 'android', 'ios', 'flutter'],
            'مواقع_ويب': ['موقع', 'ويب', 'web', 'website', 'html', 'css', 'javascript', 'pwa'],
            'iot': ['انترنت الأشياء', 'iot', 'internet of things', 'استشعار'],
            'تحليل_بيانات': ['تحليل', 'إحصاء', 'data analysis', 'statistics', 'visualization', 'power bi'],
        }
        
        self.context_triggers = {
            'supervisor': ['مشرف', 'الدكتور', 'دكتور', 'استاذ', 'أستاذ', 'للدكتور', 'بإشراف', 'اشراف', 'لأستاذ', 'استاذة', 'للدكتورة', 'دكتورة'],
            'student': ['طالب', 'الطالب', 'للطالب', 'بواسطة'],
            'department': ['قسم', 'بقسم', 'في قسم'],
            'year': ['سنة', 'عام', 'في سنة', 'لسنة']
        }
        
        # --- الإضافة الجديدة: قائمة بالكلمات العامة التي يجب تجاهلها ---
        self.stop_words = ['كل', 'جميع', 'مشاريع', 'مشروع', 'ابحث', 'عن', 'في', 'اريد', 'أريد', 'بحث', 'تخرج', 'graduation', 'project']

    def extract_search_terms(self, query):
        """
        دالة ذكية ومطورة لاستخراج المصطلحات والسياق من النص المدخل.
        """
        original_query = query # نحتفظ بالنسخة الأصلية للاستخدام لاحقاً
        query_lower = query.strip().lower()

        extracted_terms = {
            'supervisor_names': [],
            'student_names': [],
            'departments': [],
            'years': [],
            'general_terms': []
        }
        
        # متغير لتتبع ما إذا تم العثور على محددات قوية
        found_specific_filter = False

        # الخطوة 1: استخراج الكيانات المحددة (مشرف، طالب، قسم، سنة)
        for context, triggers in self.context_triggers.items():
            for trigger in triggers:
                match = re.search(fr'\b{trigger}\s+([\u0600-\u06FF\w]+(?:\s+[\u0600-\u06FF\w]+)?)', original_query, re.IGNORECASE)
                if match:
                    found_specific_filter = True
                    entity_name = match.group(1).strip()
                    if context == 'supervisor':
                        extracted_terms['supervisor_names'].append(entity_name)
                    elif context == 'student':
                        extracted_terms['student_names'].append(entity_name)
                    elif context == 'department':
                        for dept_key, dept_synonyms in self.keywords_map.items():
                            if entity_name.lower() in [s.lower() for s in dept_synonyms]:
                                extracted_terms['departments'].append(dept_key)
                                break
                    elif context == 'year':
                        year_match = re.search(r'\d{4}', entity_name)
                        if year_match:
                            extracted_terms['years'].append(year_match.group(0))
                    
                    original_query = original_query.replace(match.group(0), '', 1)

        # الخطوة 2: استخراج الأقسام والسنوات المتبقية
        found_years = re.findall(r'\b(20[1-2][0-9])\b', original_query)
        if found_years:
            found_specific_filter = True
            extracted_terms['years'].extend(found_years)
            for year in found_years:
                original_query = original_query.replace(year, '')
            
        for category, keywords in self.keywords_map.items():
            if category.startswith(('علوم', 'نظم', 'هندسة', 'وسائط', 'شبكات')):
                 for keyword in keywords:
                    if keyword.lower() in query_lower:
                        found_specific_filter = True
                        extracted_terms['departments'].append(category)
                        original_query = re.sub(re.escape(keyword), '', original_query, flags=re.IGNORECASE)

        # الخطوة 3: ما تبقى من النص يعتبر مصطلحات عامة
        remaining_words = original_query.strip().split()
        for word in remaining_words:
            # --- تعديل: تجاهل كلمات التوقف ---
            if len(word) > 2 and not word.isdigit() and word.lower() not in self.stop_words:
                extracted_terms['general_terms'].append(word)
        
        # إذا لم يتم إيجاد أي فلتر مخصص، اعتبر كل الكلمات كمصطلحات عامة
        if not found_specific_filter:
             extracted_terms['general_terms'] = [w for w in query_lower.split() if len(w) > 2]


        # إزالة التكرار
        for key, value in extracted_terms.items():
            extracted_terms[key] = list(set(value))

        return extracted_terms
    
    # دالة build_dynamic_sparql تبقى كما هي، لا تحتاج لتغيير
    def build_dynamic_sparql(self, search_terms):
        """
        بناء استعلام SPARQL دقيق جدًا بناءً على الفهم السياقي للمدخلات.
        """
        base_query = '''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?department ?year ?abstract ?pdf 
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
            OPTIONAL { ?project gpo:hasFinalFile ?pdf . }
        '''
        
        filters = []
        
        if search_terms['departments']:
            dept_filters = [f'REGEX(?department, "{dept.replace("_", " ")}", "i")' for dept in search_terms['departments']]
            filters.append(f"({' || '.join(dept_filters)})")
        
        if search_terms['years']:
            year_filters = [f'STR(?year) = "{year}"' for year in search_terms['years']]
            filters.append(f"({' || '.join(year_filters)})")

        if search_terms['supervisor_names']:
            sup_filters = [f'REGEX(?supervisorName, "{name}", "i")' for name in search_terms['supervisor_names']]
            filters.append(f"({' || '.join(sup_filters)})")
            
        if search_terms['student_names']:
            stu_filters = [f'REGEX(?students, "{name}", "i")' for name in search_terms['student_names']]
            filters.append(f"({' || '.join(stu_filters)})")

        if search_terms['general_terms']:
            text_filters = []
            for term in search_terms['general_terms']:
                term_filter_group = f'((REGEX(LCASE(STR(?title)), LCASE("{term}"))) || (BOUND(?abstract) && REGEX(LCASE(STR(?abstract)), LCASE("{term}"))))'
                text_filters.append(term_filter_group)
            if text_filters:
              filters.append(f"({' && '.join(text_filters)})")
                
        if filters:
            base_query += f'\n            FILTER ({" && ".join(filters)})'
        
        base_query += '\n        }\n        GROUP BY ?project ?title ?department ?year ?abstract ?pdf ?supervisorName\n        ORDER BY DESC(?year)'
        
        return base_query


# ... باقي الكود (search_engine, search, api_search) يبقى كما هو ...
search_engine = SmartSearchEngine()

@search_bp.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search_projects.html')
    
    query_text = request.form.get('query', '').strip()
    
    if not query_text:
        return render_template('results.html', results=[], query=query_text, debug_info="لم يتم إدخال أي نص للبحث")
    
    try:
        search_terms = search_engine.extract_search_terms(query_text)
        sparql_query = search_engine.build_dynamic_sparql(search_terms)
        
        response = requests.post(
            'http://localhost:3030/graduation/sparql',
            data={'query': sparql_query},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=30
        )
        
        debug_info = {
            'extracted_terms': search_terms,
            'sparql_query': sparql_query,
            'response_status': response.status_code
        }
        
        if response.ok:
            data = response.json()
            results = []
            
            if 'results' in data and 'bindings' in data['results']:
                for row in data['results']['bindings']:
                    result = {
                        'title': row.get('title', {}).get('value', 'غير محدد'),
                        'department': row.get('department', {}).get('value', 'غير محدد'),
                        'year': row.get('year', {}).get('value', 'غير محدد'),
                        'abstract': row.get('abstract', {}).get('value', 'غير متوفر'),
                        'pdf': row.get('pdf', {}).get('value', ''),
                        'students': row.get('students', {}).get('value', 'غير محدد'),
                        'supervisor': row.get('supervisorName', {}).get('value', 'غير محدد')
                    }
                    results.append(result)
            
            return render_template('results.html', 
                                 results=results, 
                                 query=query_text,
                                 debug_info=debug_info)
        else:
            debug_info['error'] = f"خطأ في الاستعلام: {response.status_code} - {response.text}"
            return render_template('results.html', results=[], query=query_text, debug_info=debug_info)
    
    except requests.exceptions.ConnectionError:
        error_msg = "لا يمكن الاتصال بخادم Fuseki. تأكد من تشغيل الخادم على المنفذ 3030"
        return render_template('results.html', results=[], query=query_text, debug_info={'error': error_msg})
    
    except Exception as e:
        error_msg = f"خطأ غير متوقع: {str(e)}"
        return render_template('results.html', results=[], query=query_text, debug_info={'error': error_msg})

@search_bp.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint للبحث (للاستخدام المستقبلي)"""
    data = request.get_json()
    query_text = data.get('query', '').strip()
    
    if not query_text:
        return jsonify({'error': 'لم يتم إدخال نص للبحث', 'results': []})
    
    try:
        search_terms = search_engine.extract_search_terms(query_text)
        sparql_query = search_engine.build_dynamic_sparql(search_terms)
        
        response = requests.post(
            'http://localhost:3030/graduation/sparql',
            data={'query': sparql_query},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=30
        )
        
        if response.ok:
            data = response.json()
            results = []
            
            if 'results' in data and 'bindings' in data['results']:
                for row in data['results']['bindings']:
                    result = {
                        'title': row.get('title', {}).get('value', 'غير محدد'),
                        'department': row.get('department', {}).get('value', 'غير محدد'),
                        'year': row.get('year', {}).get('value', 'غير محدد'),
                        'abstract': row.get('abstract', {}).get('value', 'غير متوفر'),
                        'pdf': row.get('pdf', {}).get('value', ''),
                        'students': row.get('students', {}).get('value', 'غير محدد'),
                        'supervisor': row.get('supervisorName', {}).get('value', 'غير محدد')
                    }
                    results.append(result)
            
            return jsonify({
                'results': results,
                'query': query_text,
                'extracted_terms': search_terms
            })
        else:
            return jsonify({'error': f'خطأ في الاستعلام: {response.status_code}', 'results': []})
    
    except Exception as e:
        return jsonify({'error': f'خطأ: {str(e)}', 'results': []})