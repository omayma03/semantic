#!/bin/bash

# سكريبت لتشغيل النظام بالكامل

echo "🚀 بدء تشغيل نظام البوابة المعرفية..."

FUSEKI_VERSION="5.4.0"
FUSEKI_DIR="apache-jena-fuseki-${FUSEKI_VERSION}"
FUSEKI_TAR="apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz"
# تم تحديث الرابط الصحيح لإصدار 5.4.0
FUSEKI_URL="https://dlcdn.apache.org/jena/binaries/${FUSEKI_TAR}"

# التحقق من وجود Fuseki
if [ ! -d "${FUSEKI_DIR}" ]; then
    echo "📥 تحميل Apache Jena Fuseki الإصدار ${FUSEKI_VERSION}..."
    # استخدام curl بدلاً من wget للتحميل
    curl -L -o "${FUSEKI_TAR}" "${FUSEKI_URL}"
    if [ $? -ne 0 ]; then
        echo "❌ فشل في تحميل Fuseki. يرجى التحقق من اتصال الإنترنت أو الرابط." >&2
        exit 1
    fi
    
    echo "📦 فك ضغط Fuseki..."
    tar -xzf "${FUSEKI_TAR}"
    if [ $? -ne 0 ]; then
        echo "❌ فشل في فك ضغط Fuseki." >&2
        exit 1
    fi
    echo "✅ تم تحميل Fuseki بنجاح"
else
    echo "✅ Fuseki موجود بالفعل."
fi

# تشغيل Fuseki في الخلفية
echo "🔧 تشغيل خادم Fuseki..."
cd "${FUSEKI_DIR}"
nohup ./fuseki-server --update --mem /graduation > fuseki.log 2>&1 &
FUSEKI_PID=$!
cd ..

# انتظار تشغيل Fuseki
echo "⏳ انتظار تشغيل Fuseki (5 ثوانٍ )..."
sleep 5

# رفع البيانات
echo "📊 رفع بيانات الأنطولوجيا..."
curl -X PUT \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/projects_converted.ttl \
  http://localhost:3030/graduation?default

if [ $? -eq 0 ]; then
    echo "✅ تم رفع البيانات بنجاح"
else
    echo "❌ فشل في رفع البيانات. تأكد من أن Fuseki يعمل وأن ملف الأنطولوجيا موجود." >&2
    # يمكن أن يكون Fuseki لم يبدأ بعد أو هناك مشكلة في المسار
fi

# تثبيت المتطلبات
echo "📦 تثبيت المتطلبات..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ فشل في تثبيت المتطلبات. تأكد من وجود Python و pip." >&2
fi

echo "🎉 النظام جاهز للتشغيل!"
echo "🌐 لتشغيل التطبيق: python app.py"
echo "🔍 رابط البحث: http://localhost:5000/search"
echo "⚙️  واجهة Fuseki: http://localhost:3030"
echo "🛑 لإيقاف Fuseki: kill $FUSEKI_PID"
