import re
import string
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class EnhancedDomainDetector:
    """فئة محسنة لاستخلاص الكلمات المفتاحية وتحديد المجال"""
    
    def __init__(self):
        # المجالات والكلمات المفتاحية المقترنة بها (محسنة)
        self.domain_keywords = {
            "الذكاء_الاصطناعي": [
                "ذكاء", "اصطناعي", "تصنيف", "تنبؤ", "neural", "machine", "learning", 
                "خوارزمية", "شبكات عصبية", "CNN", "ML", "AI", "تعلم آلة", "تعلم عميق",
                "deep learning", "tensorflow", "pytorch", "كشف", "تمييز", "نمذجة",
                "خوارزميات ذكية", "معالجة ذكية", "نظام ذكي", "تحليل ذكي"
            ],
            "تقنيات_الويب": [
                "web", "موقع", "منصة", "html", "css", "javascript", "تطبيق ويب", 
                "نظام إلكتروني", "تطبيق إلكتروني", "بوابة", "إنترنت", "متصفح",
                "frontend", "backend", "fullstack", "react", "angular", "vue",
                "node.js", "php", "asp.net", "django", "flask", "واجهة ويب"
            ],
            "الشبكات": [
                "بروتوكول", "شبكة", "IP", "OSPF", "EIGRP", "TCP", "UDP", "MPLS", 
                "QoS", "Traffic", "routing", "switching", "شبكات", "اتصالات",
                "network", "cisco", "juniper", "firewall", "vpn", "lan", "wan"
            ],
            "الأنظمة_المدمجة": [
                "arduino", "روبوت", "حساس", "استشعار", "ميكروكنترولر", "ESP32", 
                "لوحة تحكم", "hardware", "جهاز ذكي", "لوحة", "embedded", "raspberry pi",
                "sensors", "actuators", "microcontroller", "firmware", "iot device"
            ],
            "تنقيب_البيانات": [
                "تحليل", "تنقيب", "clustering", "association", "قواعد", "بيانات ضخمة", 
                "Power BI", "أنماط", "Dashboards", "data mining", "big data", "analytics",
                "visualization", "tableau", "statistics", "إحصائيات", "تحليل بيانات"
            ],
            "تطبيقات_الموبايل": [
                "هاتف", "تطبيق موبايل", "تطبيق جوال", "محمول", "android", "ios", 
                "flutter", "Dart", "تطبيق هاتف", "mobile", "smartphone", "kotlin",
                "swift", "react native", "xamarin", "cordova", "ionic"
            ],
            "إنترنت_الأشياء": [
                "إنترنت الأشياء", "IOT", "MQTT", "CoAP", "لوحة تحكم", "ESP", "COOJA", 
                "اتصال ذكي", "جهاز ذكي", "حساس ذكي", "internet of things", "smart home",
                "smart city", "connected devices", "wireless", "bluetooth", "wifi"
            ],
            "معالجة_اللغة_الطبيعية": [
                "تحليل مشاعر", "معالجة اللغة", "اللغة الطبيعية", "TF-IDF", "BERT", 
                "LSTM", "لهجة", "تلخيص", "نصوص", "NLP", "sentiment analysis", "chatbot",
                "text mining", "language model", "tokenization", "stemming", "parsing"
            ],
            "التعليم_الإلكتروني": [
                "تعليمي", "أطفال", "تعليم", "تفاعلي", "H5P", "تعليم إلكتروني", "قصة", 
                "أنشطة", "تدريب", "مقرر", "e-learning", "lms", "moodle", "scorm",
                "educational", "learning management", "online course", "virtual classroom"
            ],
            "أمن_المعلومات": [
                "كلمات السر", "أمان", "security", "graphic password", "authentication", 
                "تشفير", "هجمات", "اختراق", "cybersecurity", "encryption", "firewall",
                "malware", "vulnerability", "penetration testing", "digital forensics"
            ],
            "معالجة_الصور": [
                "صور", "معالجة الصور", "تحسين الصور", "تحليل الصور", "Image", "Vision", 
                "OCR", "تصوير", "تصنيف الصور", "computer vision", "opencv", "image processing",
                "pattern recognition", "feature extraction", "segmentation"
            ],
            "خوارزميات_الرسم_البياني": [
                "graph", "بيانات مترابطة", "خوارزمية جراف", "روابط", "علاقات", 
                "تمثيل بياني", "Graph Mining", "network analysis", "social network",
                "shortest path", "minimum spanning tree", "graph theory"
            ],
            "خوارزميات_التحسين": [
                "خوارزميات التحسين", "Optimization", "خوارزميات ذكية", "حل أمثل", 
                "المسارات المثلى", "metaheuristic", "genetic algorithm", "simulated annealing",
                "particle swarm", "ant colony", "optimization algorithms"
            ],
            "الواقع_المعزز": [
                "AR", "واقع معزز", "الواقع الافتراضي", "3D", "XR", "واقع افتراضي", 
                "تطبيق ثلاثي الأبعاد", "augmented reality", "virtual reality", "mixed reality",
                "unity", "unreal engine", "3d modeling", "immersive"
            ]
        }
        
        # كلمات الإيقاف العربية والإنجليزية
        self.arabic_stopwords = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
            'التي', 'الذي', 'التي', 'اللذان', 'اللتان', 'اللذين', 'اللتين',
            'هو', 'هي', 'هم', 'هن', 'أنت', 'أنتم', 'أنتن', 'أنا', 'نحن',
            'كان', 'كانت', 'كانوا', 'كن', 'يكون', 'تكون', 'يكونوا', 'تكن',
            'له', 'لها', 'لهم', 'لهن', 'لي', 'لك', 'لنا', 'لكم', 'لكن',
            'قد', 'لقد', 'كل', 'بعض', 'جميع', 'كلا', 'كلتا', 'بين', 'خلال',
            'أم', 'أو', 'إما', 'لكن', 'لكن', 'غير', 'سوى', 'إلا', 'ما عدا',
            'ما خلا', 'حاشا', 'ليس', 'ليست', 'ليسوا', 'لسن', 'ما', 'لا', 'لن', 'لم'
        }
        
        self.english_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
    
    def preprocess_arabic_text(self, text):
        """معالجة النص العربي"""
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u0652]', '', text)
        
        # توحيد الألف
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # توحيد التاء المربوطة والهاء
        text = re.sub(r'[ةه]', 'ه', text)
        
        # توحيد الياء
        text = re.sub(r'[يى]', 'ي', text)
        
        return text
    
    def extract_keywords_enhanced(self, text, top_k=10):
        """استخلاص الكلمات المفتاحية المحسن"""
        # معالجة النص
        processed_text = self.preprocess_arabic_text(text)
        
        # تقسيم النص إلى كلمات
        words = re.findall(r'\b\w+\b', processed_text.lower())
        
        # إزالة كلمات الإيقاف والكلمات القصيرة
        filtered_words = [
            word for word in words 
            if len(word) > 2 
            and word not in self.arabic_stopwords 
            and word not in self.english_stopwords
            and not word.isdigit()
        ]
        
        # حساب تكرار الكلمات
        word_freq = Counter(filtered_words)
        
        # استخدام TF-IDF للكلمات الأكثر أهمية
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 2),
                stop_words=None  # نحن نتعامل مع كلمات الإيقاف يدوياً
            )
            
            # تحضير النص للـ TF-IDF
            clean_text = ' '.join(filtered_words)
            if clean_text.strip():
                tfidf_matrix = vectorizer.fit_transform([clean_text])
                feature_names = vectorizer.get_feature_names_out()
                tfidf_scores = tfidf_matrix.toarray()[0]
                
                # دمج نتائج TF-IDF مع تكرار الكلمات
                tfidf_dict = dict(zip(feature_names, tfidf_scores))
                
                # حساب نقاط مركبة
                combined_scores = {}
                for word in word_freq:
                    freq_score = word_freq[word] / max(word_freq.values())
                    tfidf_score = tfidf_dict.get(word, 0)
                    combined_scores[word] = (freq_score * 0.4) + (tfidf_score * 0.6)
                
                # ترتيب الكلمات حسب النقاط المركبة
                sorted_words = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
                keywords = [word for word, score in sorted_words[:top_k]]
            else:
                # في حالة عدم وجود كلمات صالحة، استخدم التكرار فقط
                keywords = [word for word, count in word_freq.most_common(top_k)]
                
        except Exception as e:
            print(f"خطأ في TF-IDF: {e}")
            # العودة إلى التكرار البسيط في حالة الخطأ
            keywords = [word for word, count in word_freq.most_common(top_k)]
        
        return keywords
    
    def detect_domain_enhanced(self, keywords, title=""):
        """تحديد المجال المحسن"""
        # دمج الكلمات المفتاحية مع العنوان
        all_text = ' '.join(keywords + [title]).lower()
        all_text = self.preprocess_arabic_text(all_text)
        
        domain_scores = {}
        
        for domain, terms in self.domain_keywords.items():
            score = 0
            matched_terms = []
            
            for term in terms:
                term_lower = term.lower()
                term_processed = self.preprocess_arabic_text(term_lower)
                
                # البحث عن التطابق الدقيق
                if term_processed in all_text:
                    score += 2
                    matched_terms.append(term)
                # البحث عن التطابق الجزئي
                elif any(term_processed in keyword for keyword in keywords):
                    score += 1
                    matched_terms.append(term)
                # البحث في العنوان (وزن أعلى)
                elif term_processed in self.preprocess_arabic_text(title.lower()):
                    score += 3
                    matched_terms.append(term)
            
            domain_scores[domain] = {
                'score': score,
                'matched_terms': matched_terms
            }
        
        # العثور على أفضل مجال
        best_domain = max(domain_scores, key=lambda x: domain_scores[x]['score'])
        best_score = domain_scores[best_domain]['score']
        
        # إذا كان أفضل نقاط منخفض جداً، اعتبره غير مصنف
        if best_score < 1:
            return {
                'domain': "غير_مصنف",
                'confidence': 0,
                'matched_terms': [],
                'all_scores': domain_scores
            }
        
        # حساب مستوى الثقة
        total_possible_score = len(self.domain_keywords[best_domain]) * 3
        confidence = min(best_score / total_possible_score, 1.0)
        
        return {
            'domain': best_domain,
            'confidence': confidence,
            'matched_terms': domain_scores[best_domain]['matched_terms'],
            'all_scores': domain_scores
        }
    
    def get_domain_suggestions(self, keywords, title="", top_n=3):
        """الحصول على اقتراحات متعددة للمجالات"""
        domain_result = self.detect_domain_enhanced(keywords, title)
        all_scores = domain_result['all_scores']
        
        # ترتيب المجالات حسب النقاط
        sorted_domains = sorted(
            all_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        suggestions = []
        for domain, data in sorted_domains[:top_n]:
            if data['score'] > 0:
                total_possible = len(self.domain_keywords[domain]) * 3
                confidence = min(data['score'] / total_possible, 1.0)
                suggestions.append({
                    'domain': domain,
                    'score': data['score'],
                    'confidence': confidence,
                    'matched_terms': data['matched_terms']
                })
        
        return suggestions

# إنشاء مثيل عام للاستخدام
enhanced_detector = EnhancedDomainDetector()

# الدوال المتوافقة مع الكود الحالي
def extract_keywords(text, top_k=10):
    """دالة متوافقة مع الكود الحالي"""
    return enhanced_detector.extract_keywords_enhanced(text, top_k)

def detect_domain(keywords, title=""):
    """دالة متوافقة مع الكود الحالي"""
    result = enhanced_detector.detect_domain_enhanced(keywords, title)
    return result['domain']

def get_detailed_domain_analysis(text, title=""):
    """دالة جديدة للحصول على تحليل مفصل"""
    keywords = enhanced_detector.extract_keywords_enhanced(text)
    domain_result = enhanced_detector.detect_domain_enhanced(keywords, title)
    suggestions = enhanced_detector.get_domain_suggestions(keywords, title)
    
    return {
        'keywords': keywords,
        'primary_domain': domain_result,
        'domain_suggestions': suggestions,
        'text_length': len(text.split()),
        'processed_successfully': True
    }

