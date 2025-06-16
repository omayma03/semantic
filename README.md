# تشغيل خادم Apache Jena Fuseki

## الخطوات:

### 1. تحميل وتشغيل Fuseki:
```bash
# تحميل Fuseki (إذا لم يكن موجوداً)
wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.9.0.tar.gz
tar -xzf apache-jena-fuseki-4.9.0.tar.gz
cd apache-jena-fuseki-4.9.0

# تشغيل الخادم
./fuseki-server --update --mem /graduation
```

### 2. رفع البيانات:
```bash
# رفع ملف الأنطولوجيا
curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/projects_converted.ttl \
  http://localhost:3030/graduation/data
```

### 3. تشغيل التطبيق:
```bash
pip install -r requirements.txt
python app.py
```

### 4. اختبار البحث:
- افتح المتصفح على: http://localhost:5000/search
- جرب البحث بكلمات مثل:
  - "ذكاء اصطناعي"
  - "موبايل"
  - "2024"
  - "علوم الحاسوب"
  - "أمن المعلومات"

## ملاحظات:
- تأكد من تشغيل Fuseki قبل تشغيل التطبيق
- يمكن الوصول لواجهة Fuseki على: http://localhost:3030
- البيانات محفوظة في memory، ستحتاج لإعادة رفعها عند إعادة تشغيل Fuseki

