from flask import Blueprint, render_template, request, redirect, flash, jsonify
import os, uuid
import requests
from logic.rdf_generator import create_project_rdf
from logic.auto_detect_domain import extract_keywords, detect_domain
from logic.duplicate_checker import DuplicateChecker

submit_bp = Blueprint("submit_bp", __name__)

pending_projects = []  # Temporary in-memory project storage

@submit_bp.route("/", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        # Read form fields
        student = request.form["student_name"]
        group = request.form.get("group_members", "")
        title = request.form["title"]
        abstract = request.form["abstract"]
        supervisor = request.form["supervisor_name"]
        department = request.form["department"]
        year = request.form["academic_year"]
        pdf = request.files["pdf_file"]

        # تحضير قائمة الطلاب
        students = [student]
        if group:
            # تقسيم أسماء الطلاب الإضافيين (مفصولة بفواصل أو أسطر جديدة)
            additional_students = [
                s.strip() for s in group.replace("\n", ",").split(",") if s.strip()
            ]
            students.extend(additional_students)

        # التحقق من تكرار المشروع باستخدام SPARQL
        duplicate_checker = DuplicateChecker()
        duplicate_result = duplicate_checker.check_duplicate_project(
            title, supervisor, students
        )

        # إذا كان المشروع مكرراً، رفض التقديم وإظهار رسالة خطأ
        if duplicate_result["is_duplicate"]:
            duplicate_summary = duplicate_checker.get_duplicate_summary(duplicate_result)
            flash(
                f"❌ تم رفض المشروع بسبب التكرار. {duplicate_summary['details'][0]}",
                "error",
            )
            return render_template(
                "submit_project.html",
                duplicate_result=duplicate_result,
                form_data=request.form,
            )

        # Save PDF file to uploads/ folder
        filename = str(uuid.uuid4()) + ".pdf"
        path = os.path.join("uploads", filename)
        pdf.save(path)

        # Prevent duplicate submission in memory (same student and title)
        for p in pending_projects:
            if p["title"] == title and p["student"] == student:
                flash("هذا المشروع تم تقديمه مسبقاً في هذه الجلسة.", "warning")
                return redirect("/submit")

        # Extract keywords and detect domain from title + abstract
        full_text = title + " " + abstract
        keywords = extract_keywords(full_text)
        domain = detect_domain(keywords)

        # Prepare data for RDF generation
        form_data = {
            "student": student,
            "group": group,
            "students": students,
            "title": title,
            "abstract": abstract,
            "supervisor": supervisor,
            "department": department,
            "year": year,
            "pdf": f"http://localhost:5000/{path}",
            "keywords": keywords,
            "domain": domain,
            "status": "pending",  # حالة المشروع: معلق للاعتماد
            "duplicate_check": duplicate_result,
        }

        # لا نرسل البيانات إلى Fuseki مباشرة، بل نحفظها للاعتماد
        # Generate RDF for preview but don't send to Fuseki yet
        try:
            rdf_data = create_project_rdf(form_data)
            form_data["rdf_preview"] = rdf_data
        except Exception as e:
            print("Error while generating RDF preview:", e)
            form_data["rdf_preview"] = None

        # Temporarily store the project for approval
        pending_projects.append(form_data)

        # إعداد رسالة النجاح مع التحذيرات إن وجدت
        success_message = "✅ تم تقديم المشروع بنجاح. في انتظار الاعتماد."
        if duplicate_result["warnings"]:
            warning_messages = [w["message"] for w in duplicate_result["warnings"]]
            success_message += f" تحذيرات: {'; '.join(warning_messages)}"

        flash(success_message, "success")
        return redirect("/submit")

    return render_template("submit_project.html")


@submit_bp.route("/check-duplicate", methods=["POST"])
def check_duplicate():
    """API endpoint للتحقق من تكرار المشروع قبل التقديم"""
    data = request.get_json()

    title = data.get("title", "").strip()
    supervisor = data.get("supervisor", "").strip()
    students = data.get("students", [])

    if not title or not supervisor:
        return jsonify({"error": "العنوان واسم المشرف مطلوبان"}), 400

    duplicate_checker = DuplicateChecker()
    duplicate_result = duplicate_checker.check_duplicate_project(
        title, supervisor, students
    )
    duplicate_summary = duplicate_checker.get_duplicate_summary(duplicate_result)

    return jsonify({"duplicate_result": duplicate_result, "summary": duplicate_summary})


@submit_bp.route("/pending-projects")
def view_pending_projects():
    """عرض المشاريع المعلقة للاعتماد"""
    return render_template("pending_projects.html", projects=pending_projects)


