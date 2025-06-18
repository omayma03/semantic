

echo "🚀 بدء تشغيل نظام البوابة المعرفية..."

# تثبيت المتطلبات النظامية
echo "🔽 تثبيت OpenJDK 17..."
sudo apt-get update && sudo apt-get install -y openjdk-17-jdk

FUSEKI_VERSION="5.4.0"
FUSEKI_DIR="apache-jena-fuseki-${FUSEKI_VERSION}"
FUSEKI_TAR="apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz"
FUSEKI_URL="https://dlcdn.apache.org/jena/binaries/${FUSEKI_TAR}"

if [ ! -d "${FUSEKI_DIR}" ]; then
    echo "📥 تحميل Fuseki..."
    curl -L -o "${FUSEKI_TAR}" "${FUSEKI_URL}" || {
        echo "❌ فشل في تحميل Fuseki" >&2
        exit 1
    }
    
    echo "📦 فك ضغط Fuseki..."
    tar -xzf "${FUSEKI_TAR}" || {
        echo "❌ فشل في فك الضغط" >&2
        exit 1
    }
    echo "✅ تم تحميل Fuseki"
else
    echo "✅ Fuseki موجود"
fi

# منح صلاحيات التنفيذ
chmod +x "${FUSEKI_DIR}/fuseki-server"

echo "🔧 تشغيل خادم Fuseki..."
cd "${FUSEKI_DIR}"
nohup ./fuseki-server --update --mem graduation > fuseki.log 2>&1 &
FUSEKI_PID=$!
cd ..

echo "⏳ انتظار تهيئة Fuseki (25 ثانية)..."
sleep 25  # زمن انتظار أكبر

echo "📊 رفع بيانات الأنطولوجيا..."
curl -X PUT \
     -H "Content-Type: text/turtle" \
     --data-binary @ontology/projects_converted.ttl \
     http://localhost:3030/graduation/data || {
    echo "❌ فشل في رفع البيانات" >&2
}

echo "📦 تثبيت متطلبات بايثون..."
pip install -r requirements.txt
pip install scikit-learn  # تأكيد تثبيت المكتبة

echo "🎉 النظام جاهز!"
echo "🌐 تشغيل التطبيق: python app.py"
echo "🔍 رابط البحث: http://localhost:5000/search"
echo "⚙️  Fuseki: http://localhost:3030"
echo "🛑 إيقاف Fuseki: kill $FUSEKI_PID"