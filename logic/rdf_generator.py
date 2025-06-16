from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

GPO = Namespace("http://www.semanticweb.org/pc/ontologies/2025/5AcademicGraduationProjectsOntology/")

def create_project_rdf(data):
    """إنشاء RDF للمشروع مع الكلمات المفتاحية والمجال"""
    g = Graph()
    g.bind("gpo", GPO)

    # URI فريد للمشروع
    project_title_clean = data['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
    project_uri = URIRef(f"http://example.org/project/{project_title_clean}")

    # إضافة المشروع الأساسي
    g.add((project_uri, RDF.type, GPO.Project))
    g.add((project_uri, GPO.hasProjectName, Literal(data['title'])))
    g.add((project_uri, GPO.hasAbstract, Literal(data['abstract'])))
    g.add((project_uri, GPO.hasAcademicYear, Literal(data['year'], datatype=XSD.gYear)))
    g.add((project_uri, GPO.hasFinalFile, Literal(data['pdf'])))

    # إضافة الكلمات المفتاحية
    if 'keywords' in data and data['keywords']:
        for keyword in data['keywords']:
            if keyword and keyword.strip():
                keyword_uri = URIRef(f"http://example.org/keyword/{keyword.replace(' ', '_')}")
                g.add((project_uri, GPO.hasKeyword, keyword_uri))
                g.add((keyword_uri, RDF.type, GPO.Keyword))
                g.add((keyword_uri, GPO.hasKeywordText, Literal(keyword)))

    # إضافة المجال
    if 'domain' in data and data['domain']:
        domain_uri = URIRef(f"http://example.org/domain/{data['domain'].replace(' ', '_')}")
        g.add((project_uri, GPO.belongsToDomain, domain_uri))
        g.add((domain_uri, RDF.type, GPO.Domain))
        g.add((domain_uri, GPO.hasDomainName, Literal(data['domain'])))

    # إضافة حالة المشروع (معلق، معتمد، مرفوض)
    if 'status' in data:
        g.add((project_uri, GPO.hasStatus, Literal(data['status'])))

    # الطالب الرئيسي
    student_name_clean = data['student'].replace(' ', '_').replace('/', '_')
    student_uri = URIRef(f"http://example.org/student/{student_name_clean}")
    g.add((project_uri, GPO.hasEnrolledStudent, student_uri))
    g.add((student_uri, RDF.type, GPO.Student))
    g.add((student_uri, GPO.hasName, Literal(data['student'])))

    # أعضاء المجموعة (إن وجدوا)
    if 'students' in data and len(data['students']) > 1:
        # تخطي الطالب الأول لأنه تم إضافته بالفعل
        for member in data['students'][1:]:
            if member and member.strip():
                member_name_clean = member.replace(' ', '_').replace('/', '_')
                member_uri = URIRef(f"http://example.org/student/{member_name_clean}")
                g.add((project_uri, GPO.hasEnrolledStudent, member_uri))
                g.add((member_uri, RDF.type, GPO.Student))
                g.add((member_uri, GPO.hasName, Literal(member)))
    elif 'group' in data and data['group']:
        # للتوافق مع الكود القديم
        members = [name.strip() for name in data['group'].replace('\n', ',').split(',') if name.strip()]
        for member in members:
            member_name_clean = member.replace(' ', '_').replace('/', '_')
            member_uri = URIRef(f"http://example.org/student/{member_name_clean}")
            g.add((project_uri, GPO.hasEnrolledStudent, member_uri))
            g.add((member_uri, RDF.type, GPO.Student))
            g.add((member_uri, GPO.hasName, Literal(member)))

    # المشرف
    supervisor_name_clean = data['supervisor'].replace(' ', '_').replace('/', '_')
    supervisor_uri = URIRef(f"http://example.org/supervisor/{supervisor_name_clean}")
    g.add((project_uri, GPO.isSupervisedBySupervisor, supervisor_uri))
    g.add((supervisor_uri, RDF.type, GPO.Supervisor))
    g.add((supervisor_uri, GPO.hasName, Literal(data['supervisor'])))

    # القسم
    dept_name_clean = data['department'].replace(' ', '_').replace('/', '_')
    dept_uri = URIRef(f"http://example.org/department/{dept_name_clean}")
    g.add((project_uri, GPO.belongsToDepartment, dept_uri))
    g.add((dept_uri, RDF.type, GPO.Department))
    g.add((dept_uri, GPO.hasName, Literal(data['department'])))

    # إضافة معلومات إضافية للتحقق من التكرار
    if 'duplicate_check' in data:
        duplicate_info = data['duplicate_check']
        if duplicate_info.get('warnings'):
            for warning in duplicate_info['warnings']:
                g.add((project_uri, GPO.hasWarning, Literal(warning['message'])))

    return g.serialize(format='turtle')

def create_keyword_rdf(keyword_text, domain=None):
    """إنشاء RDF منفصل للكلمة المفتاحية"""
    g = Graph()
    g.bind("gpo", GPO)
    
    keyword_uri = URIRef(f"http://example.org/keyword/{keyword_text.replace(' ', '_')}")
    g.add((keyword_uri, RDF.type, GPO.Keyword))
    g.add((keyword_uri, GPO.hasKeywordText, Literal(keyword_text)))
    
    if domain:
        domain_uri = URIRef(f"http://example.org/domain/{domain.replace(' ', '_')}")
        g.add((keyword_uri, GPO.belongsToDomain, domain_uri))
    
    return g.serialize(format='turtle')

def create_domain_rdf(domain_name, keywords=None):
    """إنشاء RDF منفصل للمجال"""
    g = Graph()
    g.bind("gpo", GPO)
    
    domain_uri = URIRef(f"http://example.org/domain/{domain_name.replace(' ', '_')}")
    g.add((domain_uri, RDF.type, GPO.Domain))
    g.add((domain_uri, GPO.hasDomainName, Literal(domain_name)))
    
    if keywords:
        for keyword in keywords:
            keyword_uri = URIRef(f"http://example.org/keyword/{keyword.replace(' ', '_')}")
            g.add((domain_uri, GPO.hasRelatedKeyword, keyword_uri))
    
    return g.serialize(format='turtle')

