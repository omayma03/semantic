from flask import Blueprint, render_template, request, redirect, flash, jsonify
import os, uuid
import requests
from logic.rdf_generator import create_project_rdf
from logic.auto_detect_domain import extract_keywords, detect_domain
from logic.duplicate_checker import DuplicateChecker

submit_bp = Blueprint("submit_bp", __name__)

pending_projects = []  # Temporary in-memory project storage

# في ملف routes/submit_bp.py

@submit_bp.route("/", methods=["GET", "POST"])
def submit():
    form_data = {}
    if request.method == "POST":
        try:
            student = request.form["student_name"]
            group = request.form.get("group_members", "")
            title = request.form["title"]
            abstract = request.form["abstract"]
            supervisor = request.form["supervisor_name"]
            department = request.form["department"]
            year = request.form["academic_year"]
            pdf = request.files["pdf_file"]
            form_data = request.form
        except KeyError as e:
            flash(f"خطأ في النموذج، الحقل المطلوب {e} مفقود.", "error")
            return redirect("/submit")

        students = [student.strip()]
        if group:
            additional_students = [s.strip() for s in group.replace("\n", ",").split(",") if s.strip()]
            students.extend(additional_students)

        duplicate_checker = DuplicateChecker()
        duplicate_result = duplicate_checker.check_duplicate_project(title, supervisor, students)
        
        if duplicate_result["is_duplicate"]:
            # إذا كان مكرراً، أظهر الخطأ وتوقف هنا
            flash(duplicate_result['duplicate_details']['message'], "error")
            return render_template("submit_project.html", form_data=form_data, duplicate_result=duplicate_result)

        # --- إذا لم يكن مكرراً، استمر هنا ---

        # 1. حفظ ملف PDF
        filename = str(uuid.uuid4()) + ".pdf"
        path = os.path.join("uploads", filename)
        pdf.save(path)

        # 2. تحضير بيانات المشروع
        project_data = {
            "student": student,
            "group": group,
            "students": students,
            "title": title,
            "abstract": abstract,
            "supervisor": supervisor,
            "department": department,
            "year": year,
            "pdf": f"http://localhost:5000/{path}",
            "status": "pending", # الحالة الأولية هي "معلق"
        }
        
        # 3. الإضافة إلى قائمة الانتظار فقط
        pending_projects.append(project_data)

        # 4. إظهار رسالة نجاح وإعادة التوجيه
        flash("✅ تم تقديم المشروع بنجاح وهو الآن في انتظار الاعتماد.", "success")
        return redirect("/submit")

    return render_template("submit_project.html", form_data=form_data)


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


