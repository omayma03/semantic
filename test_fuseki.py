import requests

# عنوان نقطة النهاية للاستعلام في Fuseki
FUSEKI_URL = "http://localhost:3030/graduation/sparql"

# استعلام بسيط جداً لجلب أي 10 نتائج
SIMPLE_QUERY = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"

print("--- بدء اختبار Fuseki البسيط ---")
print(f"العنوان المستهدف: {FUSEKI_URL}")

try:
    # سنستخدم طريقة GET وهي الطريقة الصحيحة
    response = requests.get(
        FUSEKI_URL,
        params={'query': SIMPLE_QUERY},
        headers={'Accept': 'application/json'}
    )

    # طباعة حالة الاستجابة (هذا هو المهم)
    print(f"\n>>> حالة الاستجابة (Status Code): {response.status_code} <<<\n")

    if response.ok:
        print("✅ نجح الاتصال! والاستعلام يعمل.")
        print("النتائج بصيغة JSON:")
        # طباعة أول 200 حرف من الاستجابة
        print(str(response.json())[:200] + "...")
    else:
        print("❌ فشل الاتصال! الخادم استجاب بخطأ.")
        print("محتوى الاستجابة:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print("\n❌ فشل حرج! لم نتمكن من الاتصال بالخادم إطلاقاً.")
    print(f"تفاصيل الخطأ: {e}")

print("\n--- انتهى الاختبار ---")