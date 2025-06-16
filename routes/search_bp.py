from flask import Blueprint, render_template, request, jsonify
import requests
import re
from urllib.parse import quote
from collections import defaultdict

search_bp = Blueprint('search_bp', __name__)

class SemanticSearchEngine:
    """محرك بحث دلالي يفهم السياق ويستفيد من الأنطولوجيا لتحسين النتائج"""
    
    def __init__(self):
        # قاموس الكلمات المفتاحية والمرادفات مع روابط دلالية
        self.semantic_map = {
            # أقسام الكلية
            'علوم_الحاسوب': {
                'synonyms': ['علوم الحاسوب', 'حاسوب', 'كمبيوتر', 'computer science', 'cs'],
                'related_domains': ['الذكاء_الاصطناعي', 'تقنيات_الويب', 'قواعد_بيانات']
            },
            'نظم_الإنترنت': {
                'synonyms': ['نظم الإنترنت', 'انترنت', 'شبكات', 'internet systems', 'networks'],
                'related_domains': ['الشبكات', 'أمن_المعلومات']
            },
            'الوسائط_المتعددة': {
                'synonyms': ['وسائط متعددة', 'ملتيميديا', 'multimedia', 'وسائط'],
                'related_domains': ['معالجة_الصور', 'الواقع_المعزز']
            },
            # مجالات تقنية
            'الذكاء_الاصطناعي': {
                'synonyms': ['ذكاء اصطناعي', 'ai', 'artificial intelligence', 'machine learning', 'تعلم آلي'],
                'related_terms': ['شبكات عصبية', 'تعلم عميق', 'تصنيف', 'تنبؤ'],
                'related_domains': ['معالجة_اللغة_الطبيعية', 'تنقيب_البيانات']
            },
            'أمن_المعلومات': {
                'synonyms': ['أمن', 'حماية', 'security', 'cybersecurity', 'أمان'],
                'related_terms': ['تشفير', 'هجمات', 'اختراق'],
                'related_domains': ['الشبكات']
            },
            'قواعد_بيانات': {
                'synonyms': ['قاعدة بيانات', 'database', 'sql', 'بيانات'],
                'related_terms': ['استعلام', 'تخزين', 'إدارة بيانات'],
                'related_domains': ['تنقيب_البيانات']
            },
            # سنوات
            'سنة': {
                'synonyms': ['2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015'],
                'related_terms': []
            },
            # كلمات عامة
            'مشروع': {
                'synonyms': ['مشروع', 'project', 'تخرج', 'graduation'],
                'related_terms': ['عمل جماعي', 'بحث']
            },
            'طالب': {
                'synonyms': ['طالب', 'student', 'دارس'],
                'related_terms': ['مجموعة', 'فريق']
            },
            'مشرف': {
                'synonyms': ['مشرف', 'supervisor', 'دكتور', 'أستاذ'],
                'related_terms': ['مرشد', 'موجه']
            }
        }
        
        # توحيد الكلمات المفتاحية لتسهيل البحث
        self.keyword_to_category = {}
        for category, data in self.semantic_map.items():
            for synonym in data['synonyms']:
                self.keyword_to_category[synonym.lower()] = category
    
    def preprocess_query(self, query):
        """معالجة النص المدخل وتنظيفه"""
        query = query.strip().lower()
        # إزالة التشكيل العربي
        query = re.sub(r'[\u064B-\u0652]', '', query)
        # توحيد الألف
        query = re.sub(r'[إأآا]', 'ا', query)
        # توحيد الياء
        query = re.sub(r'[يى]', 'ي', query)
        # إزالة الرموز الخاصة
        query = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query)
        return query
    
    def extract_semantic_terms(self, query):
        """استخراج المصطلحات الدلالية من النص المدخل"""
        processed_query = self.preprocess_query(query)
        words = processed_query.split()
        
        extracted_terms = {
            'categories': set(),
            'departments': [],
            'technical_fields': [],
            'years': [],
            'general_terms': [],
            'related_domains': set(),
            'related_terms': set(),
            'original_query': query
        }
        
        # تحديد الكلمات المفتاحية والمصطلحات المتعلقة
        for word in words:
            if word in self.keyword_to_category:
                category = self.keyword_to_category[word]
                extracted_terms['categories'].add(category)
                
                if category in ['علوم_الحاسوب', 'نظم_الإنترنت', 'الوسائط_المتعددة']:
                    extracted_terms['departments'].append(category)
                elif category in ['الذكاء_الاصطناعي', 'أمن_المعلومات', 'قواعد_بيانات']:
                    extracted_terms['technical_fields'].append(word)
                elif category == 'سنة':
                    extracted_terms['years'].append(word)
                else:
                    extracted_terms['general_terms'].append(word)
                
                # إضافة المجالات والمصطلحات المتعلقة
                if 'related_domains' in self.semantic_map[category]:
                    extracted_terms['related_domains'].update(self.semantic_map[category]['related_domains'])
                if 'related_terms' in self.semantic_map[category]:
                    extracted_terms['related_terms'].update(self.semantic_map[category]['related_terms'])
            else:
                if len(word) > 2:
                    extracted_terms['general_terms'].append(word)
        
        return extracted_terms
    
    def build_semantic_sparql(self, search_terms):
        """بناء استعلام SPARQL دلالي يستفيد من الأنطولوجيا"""
        base_query = '''
        PREFIX gpo: <http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/>
        
        SELECT DISTINCT ?project ?title ?department ?year ?abstract ?pdf 
                        (GROUP_CONCAT(DISTINCT ?studentName; separator=", ") AS ?students)
                        ?supervisorName ?relevanceScore
        WHERE {
            ?project a gpo:Project ;
                     gpo:hasProjectName ?title ;
                     gpo:belongsToDepartment ?deptEntity ;
                     gpo:hasAcademicYear ?year ;
                     gpo:hasAbstract ?abstract ;
                     gpo:hasEnrolledStudent ?studentEntity ;
                     gpo:isSupervisedBySupervisor ?supervisorEntity .
            
            ?deptEntity gpo:hasName ?department .
            ?studentEntity gpo:hasName ?studentName .
            ?supervisorEntity gpo:hasName ?supervisorName .
            
            OPTIONAL { ?project gpo:hasFinalFile ?pdf }
            OPTIONAL { ?project gpo:hasKeyword ?keyword . ?keyword gpo:hasKeywordText ?keywordText }
            OPTIONAL { ?project gpo:belongsToDomain ?domain . ?domain gpo:hasDomainName ?domainName }
            
            # تعيين درجة الأهمية بناءً على التطابقات
            BIND (
                (IF(REGEX(LCASE(STR(?title)), LCASE("{search_text}"), "i"), 5, 0) +
                 IF(REGEX(LCASE(STR(?abstract)), LCASE("{search_text}"), "i"), 3, 0) +
                 IF(REGEX(LCASE(STR(?keywordText)), LCASE("{search_text}"), "i"), 2, 0) +
                 IF(REGEX(LCASE(STR(?domainName)), LCASE("{search_text}"), "i"), 2, 0)) AS ?relevanceScore
            )
        '''
        
        filters = []
        relevance_conditions = []
        
        # فلاتر الأقسام
        if search_terms['departments']:
            dept_filters = []
            for dept in search_terms['departments']:
                dept_filters.append(f'REGEX(STR(?department), "{dept}", "i")')
            if dept_filters:
                filters.append(f"({' || '.join(dept_filters)})")
        
        # فلاتر السنوات
        if search_terms['years']:
            year_filters = []
            for year in search_terms['years']:
                year_filters.append(f'REGEX(STR(?year), "{year}")')
            if year_filters:
                filters.append(f"({' || '.join(year_filters)})")
        
        # فلاتر المصطلحات الدلالية (البحث في العنوان، الملخص، الكلمات المفتاحية، المجالات)
        all_terms = (search_terms['general_terms'] + search_terms['technical_fields'] +
                     list(search_terms['related_terms']) + list(search_terms['related_domains']))
        
        if all_terms:
            text_filters = []
            for term in set(all_terms):  # إزالة التكرار
                if len(term) > 2:
                    escaped_term = re.escape(term)
                    text_filters.append(f'REGEX(LCASE(STR(?title)), LCASE("{escaped_term}"))')
                    text_filters.append(f'REGEX(LCASE(STR(?abstract)), LCASE("{escaped_term}"))')
                    text_filters.append(f'REGEX(LCASE(STR(?keywordText)), LCASE("{escaped_term}"))')
                    text_filters.append(f'REGEX(LCASE(STR(?domainName)), LCASE("{escaped_term}"))')
            
            if text_filters:
                filters.append(f"({' || '.join(text_filters)})")
        
        # إضافة الفلاتر للاستعلام
        if filters:
            base_query += f'\n            FILTER ({" && ".join(filters)})'
        
        # إضافة شرط درجة الأهمية
        base_query += '\n            FILTER (?relevanceScore > 0)'
        
        # تنظيم النتائج
        base_query += '\n        }\n        GROUP BY ?project ?title ?department ?year ?abstract ?pdf ?supervisorName ?relevanceScore'
        base_query += '\n        ORDER BY DESC(?relevanceScore) ?title'
        
        # إضافة النص الأصلي للبحث
        base_query = base_query.format(search_text=re.escape(search_terms['original_query']))
        
        return base_query

# إنشاء محرك البحث الدلالي
semantic_search_engine = SemanticSearchEngine()

@search_bp.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search_projects.html')
    
    # الحصول على النص المدخل
    query_text = request.form.get('query', '').strip()
    
    if not query_text:
        return render_template('results.html', results=[], query=query_text, debug_info="لم يتم إدخال أي نص للبحث")
    
    try:
        # استخراج المصطلحات الدلالية
        search_terms = semantic_search_engine.extract_semantic_terms(query_text)
        
        # بناء استعلام SPARQL دلالي
        sparql_query = semantic_search_engine.build_semantic_sparql(search_terms)
        
        # تنفيذ الاستعلام
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
                        'supervisor': row.get('supervisorName', {}).get('value', 'غير محدد'),
                        'relevance_score': float(row.get('relevanceScore', {}).get('value', 0))
                    }
                    results.append(result)
            
            return render_template('results.html', 
                                 results=results, 
                                 query=query_text,
                                 debug_info=debug_info)
        else:
            error_msg = f"خطأ في الاستعلام: {response.status_code} - {response.text}"
            return render_template('results.html', 
                                 results=[], 
                                 query=query_text,
                                 debug_info={'error': error_msg})
    
    except requests.exceptions.ConnectionError:
        error_msg = "لا يمكن الاتصال بخادم Fuseki. تأكد من تشغيل الخادم على المنفذ 3030"
        return render_template('results.html', 
                             results=[], 
                             query=query_text,
                             debug_info={'error': error_msg})
    
    except Exception as e:
        error_msg = f"خطأ غير متوقع: {str(e)}"
        return render_template('results.html', 
                             results=[], 
                             query=query_text,
                             debug_info={'error': error_msg})

@search_bp.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint للبحث الدلالي"""
    data = request.get_json()
    query_text = data.get('query', '').strip()
    
    if not query_text:
        return jsonify({'error': 'لم يتم إدخال نص للبحث', 'results': []})
    
    try:
        search_terms = semantic_search_engine.extract_semantic_terms(query_text)
        sparql_query = semantic_search_engine.build_semantic_sparql(search_terms)
        
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
                        'supervisor': row.get('supervisorName', {}).get('value', 'غير محدد'),
                        'relevance_score': float(row.get('relevanceScore', {}).get('value', 0))
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

