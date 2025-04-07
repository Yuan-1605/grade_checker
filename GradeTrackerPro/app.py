import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 配置日誌記錄
logging.basicConfig(level=logging.DEBUG)

# 創建 Flask 應用
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# 初始化登入管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "請先登入才能訪問此頁面"

# 導入模型和表單，避免循環導入問題
from models import User, Class, Student, GradeItem, Grade, AccessCode, Semester
from forms import LoginForm, UserForm, ClassForm, GradeItemForm, AccessCodeForm, ExcelImportForm

# 導入工具函數
from utils import initialize_sample_data, allowed_file, process_excel_file, get_student_grades, get_classes_for_teacher

# 初始化示例數據
initialize_sample_data()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.get_by_id(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # 嘗試以教師/管理員身份登入
        from models import User, Student
        user = User.get_by_username(form.username.data)
        
        # 如果找到教師/管理員帳號且密碼符合
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        # 若非教師/管理員帳號，嘗試以學生身份登入
        # 座號(seat_number)作為帳號，學號(student_id)作為密碼
        app.logger.debug(f"嘗試學生登入: 座號={form.username.data}, 學號={form.password.data}")
        
        # 檢查所有班級中是否有此座號的學生
        for class_obj in Class.get_all():
            student = Student.get_by_seat_number(class_obj.id, form.username.data)
            if student and student.student_id == form.password.data:
                app.logger.debug(f"找到學生: {student.name}, 學號: {student.student_id}")
                # 找到學生，創建對應用戶
                user = User.get_by_username(form.username.data)
                if not user:
                    user = User.create(
                        username=student.seat_number,
                        email=f"{student.seat_number}@school.edu",
                        role="student",
                        password=student.student_id
                    )
                    app.logger.debug(f"為學生創建了新用戶: {user.username}")
                
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
        
        # 如果都沒找到匹配的用戶
        flash('帳號或密碼無效', 'danger')
    
    return render_template('login.html', form=form, title='登入系統')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_role = current_user.role
    
    if user_role == 'student':
        return redirect(url_for('student_grades'))
    elif user_role == 'teacher':
        return redirect(url_for('teacher_grades'))
    elif user_role == 'admin':
        return redirect(url_for('admin_panel'))
    
    # 未知角色的后備方案
    flash('您的帳號尚未被指派有效的角色', 'warning')
    return render_template('dashboard.html')

@app.route('/student/grades')
@login_required
def student_grades():
    if current_user.role != 'student':
        flash('您沒有權限查看此頁面', 'danger')
        return redirect(url_for('dashboard'))
    
    # 學生登入系統時，以座號作為使用者名稱，並儲存座號
    seat_number = current_user.username
    app.logger.debug(f"學生端查詢成績 - 座號: {seat_number}")
    
    # 根據座號查找所有班級中的學生
    student = None
    for class_obj in Class.get_all():
        student_found = Student.get_by_seat_number(class_obj.id, seat_number)
        if student_found:
            student = student_found
            break
    
    if not student:
        flash('找不到您的學生資料，請聯絡教師', 'warning')
        return redirect(url_for('dashboard'))
    
    app.logger.debug(f"找到學生: {student.name}, ID: {student.id}, 班級: {student.class_id}")
    
    # 取得學生成績
    grades = get_student_grades(student.id)
    
    return render_template('student_grades.html', 
                           grades=grades, 
                           student=student,
                           title='我的成績')

@app.route('/student_management')
@login_required
def student_management():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('您沒有權限查看此頁面', 'danger')
        return redirect(url_for('dashboard'))
    
    # 獲取學期
    semesters = Semester.get_all()
    selected_semester = request.args.get('semester', semesters[0] if semesters else None)
    
    # 獲取該學期的班級
    if selected_semester:
        classes = Class.get_by_teacher_and_semester(current_user.id, selected_semester)
    else:
        classes = get_classes_for_teacher(current_user.id)
    
    selected_class_id = request.args.get('class_id', None)
    if selected_class_id:
        selected_class_id = int(selected_class_id)
    elif classes:
        selected_class_id = classes[0].id
    
    selected_class = None
    students = []
    
    if selected_class_id:
        selected_class = Class.get_by_id(selected_class_id)
        if selected_class:
            students = Student.get_by_class_id(selected_class_id)
    
    return render_template('student_management.html', 
                           semesters=semesters,
                           selected_semester=selected_semester,
                           classes=classes,
                           selected_class=selected_class,
                           students=students,
                           title='學生管理')

@app.route('/teacher/grades', methods=['GET', 'POST'])
@login_required
def teacher_grades():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('您沒有權限查看此頁面', 'danger')
        return redirect(url_for('dashboard'))
    
    # 獲取學期
    semesters = Semester.get_all()
    selected_semester = request.args.get('semester', semesters[0] if semesters else None)
    
    # 獲取該學期的班級
    if selected_semester:
        classes = Class.get_by_teacher_and_semester(current_user.id, selected_semester)
    else:
        classes = get_classes_for_teacher(current_user.id)
    
    selected_class_id = request.args.get('class_id', None)
    if selected_class_id:
        selected_class_id = int(selected_class_id)
    elif classes:
        selected_class_id = classes[0].id
    
    selected_class = None
    students = []
    grade_items = []
    grades = []
    
    if selected_class_id:
        selected_class = Class.get_by_id(selected_class_id)
        if selected_class:
            students = Student.get_by_class_id(selected_class_id)
            grade_items = GradeItem.get_by_class_id(selected_class_id)
            # 獲取所有學生的所有成績
            for student in students:
                student_grades = Grade.get_by_student_id(student.id)
                grades.extend(student_grades)
    
    # 處理成績更新
    if request.method == 'POST':
        if current_user.role != 'teacher' and current_user.role != 'admin':
            return {"success": False, "message": "未授權"}, 403
        
        data = request.json
        student_id = data.get('student_id')
        grade_item_id = data.get('grade_item_id')
        value = data.get('value')
        
        try:
            grade = Grade.update_or_create(student_id, grade_item_id, value)
            return {"success": True, "message": "成績更新成功"}
        except Exception as e:
            app.logger.error(f"更新成績錯誤: {str(e)}")
            return {"success": False, "message": str(e)}, 400
    
    return render_template('teacher_grades.html', 
                           semesters=semesters,
                           selected_semester=selected_semester,
                           classes=classes,
                           selected_class=selected_class,
                           students=students,
                           grade_items=grade_items,
                           grades=grades,
                           title='管理成績')

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.get_all()
    classes = Class.get_all()
    grade_items = GradeItem.get_all()
    access_codes = AccessCode.get_all()
    
    return render_template('admin_panel.html', 
                           users=users,
                           classes=classes,
                           grade_items=grade_items,
                           access_codes=access_codes,
                           title='Admin Panel')

@app.route('/admin/users', methods=['POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        if form.user_id.data:
            # Update existing user
            user = User.get_by_id(form.user_id.data)
            if user:
                user.update(
                    username=form.username.data,
                    email=form.email.data,
                    role=form.role.data
                )
                
                if form.password.data:
                    user.set_password(form.password.data)
                    
                flash('User updated successfully', 'success')
            else:
                flash('User not found', 'danger')
        else:
            # Create new user
            if User.get_by_username(form.username.data):
                flash('Username already exists', 'danger')
            else:
                user = User.create(
                    username=form.username.data,
                    email=form.email.data,
                    role=form.role.data
                )
                user.set_password(form.password.data)
                flash('User created successfully', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/classes', methods=['POST'])
@login_required
def manage_classes():
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ClassForm()
    
    if form.validate_on_submit():
        if form.class_id.data:
            # Update existing class
            class_obj = Class.get_by_id(form.class_id.data)
            if class_obj:
                teacher = User.get_by_id(form.teacher_id.data)
                if teacher and (teacher.role == 'teacher' or teacher.role == 'admin'):
                    class_obj.update(
                        name=form.name.data,
                        teacher_id=form.teacher_id.data
                    )
                    flash('Class updated successfully', 'success')
                else:
                    flash('Invalid teacher selected', 'danger')
            else:
                flash('Class not found', 'danger')
        else:
            # Create new class
            teacher = User.get_by_id(form.teacher_id.data)
            if teacher and (teacher.role == 'teacher' or teacher.role == 'admin'):
                Class.create(
                    name=form.name.data,
                    teacher_id=form.teacher_id.data
                )
                flash('Class created successfully', 'success')
            else:
                flash('Invalid teacher selected', 'danger')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/grade_items', methods=['POST'])
@login_required
def manage_grade_items():
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard'))
    
    form = GradeItemForm()
    
    if form.validate_on_submit():
        if form.grade_item_id.data:
            # Update existing grade item
            grade_item = GradeItem.get_by_id(form.grade_item_id.data)
            if grade_item:
                grade_item.update(
                    name=form.name.data,
                    class_id=form.class_id.data,
                    max_score=form.max_score.data
                )
                flash('Grade item updated successfully', 'success')
            else:
                flash('Grade item not found', 'danger')
        else:
            # Create new grade item
            GradeItem.create(
                name=form.name.data,
                class_id=form.class_id.data,
                max_score=form.max_score.data
            )
            flash('Grade item created successfully', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/access_codes', methods=['POST'])
@login_required
def manage_access_codes():
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard'))
    
    form = AccessCodeForm()
    
    if form.validate_on_submit():
        if form.access_code_id.data:
            # Update existing access code
            access_code = AccessCode.get_by_id(form.access_code_id.data)
            if access_code:
                access_code.update(
                    code=form.code.data,
                    role=form.role.data,
                    expiry_date=form.expiry_date.data
                )
                flash('Access code updated successfully', 'success')
            else:
                flash('Access code not found', 'danger')
        else:
            # Create new access code
            AccessCode.create(
                code=form.code.data,
                role=form.role.data,
                expiry_date=form.expiry_date.data
            )
            flash('Access code created successfully', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_grades():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('You do not have permission to import grades', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ExcelImportForm()
    
    # Get classes for the user
    if current_user.role == 'admin':
        form.class_id.choices = [(c.id, c.name) for c in Class.get_all()]
    else:
        form.class_id.choices = [(c.id, c.name) for c in get_classes_for_teacher(current_user.id)]
    
    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            class_id = form.class_id.data
            try:
                results = process_excel_file(file, class_id)
                flash(f'Successfully imported {results["grades_imported"]} grades. '
                      f'Created {results["students_created"]} new students and '
                      f'{results["grade_items_created"]} new grade items.', 'success')
                
                return redirect(url_for('teacher_grades', class_id=class_id))
            except Exception as e:
                flash(f'Error processing Excel file: {str(e)}', 'danger')
                app.logger.error(f"Excel import error: {str(e)}")
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx, .xls)', 'danger')
    
    return render_template('import_grades.html', form=form, title='Import Grades')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', title='404 - Page Not Found', 
                          error_message='The page you requested was not found.'), 404

@app.route('/api/semesters', methods=['GET', 'POST'])
@login_required
def manage_semesters():
    if request.method == 'GET':
        return {"semesters": Semester.get_all()}
    
    elif request.method == 'POST':
        data = request.json
        semester = data.get('semester')
        
        if not semester:
            return {"success": False, "message": "學期不能為空"}, 400
        
        if Semester.add(semester):
            return {"success": True, "message": "學期添加成功", "semesters": Semester.get_all()}
        else:
            return {"success": False, "message": "學期已存在"}, 400

@app.route('/api/semesters/<semester>', methods=['DELETE'])
@login_required
def delete_semester(semester):
    if Semester.remove(semester):
        return {"success": True, "message": "學期刪除成功", "semesters": Semester.get_all()}
    else:
        return {"success": False, "message": "不能刪除最後一個學期"}, 400

@app.route('/api/classes', methods=['POST'])
@login_required
def create_class():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限執行此操作"}, 403
        
    data = request.json
    name = data.get('name')
    semester = data.get('semester')
    
    if not name or not semester:
        return {"success": False, "message": "班級名稱和學期不能為空"}, 400
    
    new_class = Class.create(name, current_user.id, semester)
    return {
        "success": True, 
        "message": "班級創建成功", 
        "class": {
            "id": new_class.id,
            "name": new_class.name,
            "semester": new_class.semester
        }
    }

@app.route('/api/classes/<int:class_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_class(class_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限執行此操作"}, 403
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        return {"success": False, "message": "找不到班級"}, 404
    
    if class_obj.teacher_id != current_user.id and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限編輯此班級"}, 403
    
    if request.method == 'PUT':
        data = request.json
        name = data.get('name')
        
        if not name:
            return {"success": False, "message": "班級名稱不能為空"}, 400
        
        class_obj.update(name=name)
        return {
            "success": True, 
            "message": "班級更新成功", 
            "class": {
                "id": class_obj.id,
                "name": class_obj.name,
                "semester": class_obj.semester
            }
        }
    
    elif request.method == 'DELETE':
        if Class.delete(class_id):
            return {"success": True, "message": "班級刪除成功"}
        else:
            return {"success": False, "message": "班級刪除失敗"}, 500

@app.route('/api/classes/<int:class_id>/students', methods=['GET', 'POST'])
@login_required
def manage_students(class_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限執行此操作"}, 403
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        return {"success": False, "message": "找不到班級"}, 404
    
    if class_obj.teacher_id != current_user.id and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限管理此班級的學生"}, 403
    
    if request.method == 'GET':
        students = Student.get_by_class_id(class_id)
        return {
            "students": [
                {
                    "id": student.id,
                    "name": student.name,
                    "seat_number": student.seat_number,
                    "student_id": student.student_id
                } for student in students
            ]
        }
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        seat_number = data.get('seat_number')
        student_id = data.get('student_id', "")
        
        if not name:
            return {"success": False, "message": "學生姓名不能為空"}, 400
        
        # 確保座號是字串格式
        seat_number = str(seat_number).strip()
        if '.' in seat_number:  # 移除可能的小數點部分
            seat_number = seat_number.split('.')[0]
        
        # 檢查座號是否為數字內容
        if not seat_number.isdigit():
            return {"success": False, "message": "座號必須是數字"}, 400
        
        # 如果少於5碼，補0
        if len(seat_number) < 5:
            seat_number = seat_number.zfill(5)
        
        # 處理學號格式 (如果有提供)
        if student_id:
            student_id = str(student_id).strip()
            if '.' in student_id:  # 移除可能的小數點部分
                student_id = student_id.split('.')[0]
            
            # 如果少於6碼，補0
            if student_id.isdigit() and len(student_id) < 6:
                student_id = student_id.zfill(6)
        
        # 檢查座號是否已存在
        existing_student = Student.get_by_seat_number(class_id, seat_number)
        if existing_student:
            return {"success": False, "message": f"座號 {seat_number} 已被使用"}, 400
        
        app.logger.debug(f"創建新學生: 座號={seat_number}, 姓名={name}, 學號={student_id}")
        new_student = Student.create(name, class_id, seat_number, student_id)
        return {
            "success": True, 
            "message": "學生創建成功", 
            "student": {
                "id": new_student.id,
                "name": new_student.name,
                "seat_number": new_student.seat_number,
                "student_id": new_student.student_id
            }
        }

@app.route('/api/students/batch', methods=['POST'])
@login_required
def batch_manage_students():
    try:
        # 權限檢查
        if current_user.role != 'teacher' and current_user.role != 'admin':
            return {"success": False, "message": "您沒有權限執行此操作"}, 403
        
        data = request.json
        class_id = data.get('classId')
        students_data = data.get('students', [])
        clear_existing = data.get('clearExisting', False)
        
        # 驗證輸入
        if not class_id:
            return {"success": False, "message": "請選擇班級"}, 400
        
        if not students_data:
            return {"success": False, "message": "沒有提供學生資料"}, 400
        
        # 班級存在檢查
        class_obj = Class.get_by_id(int(class_id))
        if not class_obj:
            return {"success": False, "message": "找不到班級"}, 404
        
        # 權限檢查
        if class_obj.teacher_id != current_user.id and current_user.role != 'admin':
            return {"success": False, "message": "您沒有權限管理此班級的學生"}, 403
        
        app.logger.debug(f"批次處理 {len(students_data)} 個學生，清除現有={clear_existing}")
        
        # 如果需要清除現有學生
        if clear_existing:
            students = Student.get_by_class_id(class_id)
            for student in students:
                Student.delete(student.id)
            app.logger.debug(f"已清除班級 {class_id} 中的所有學生")
        
        # 批量添加/更新學生
        created_count = 0
        updated_count = 0
        
        for student_data in students_data:
            seat_number = student_data.get('seatNumber')
            name = student_data.get('name')
            student_id_number = student_data.get('studentId')
            
            if not seat_number or not name:
                app.logger.warning(f"跳過缺少座號或姓名的學生資料: {student_data}")
                continue
            
            # 確保座號和學號格式正確
            # 座號必須是5碼數字字串
            seat_number = str(seat_number).strip()
            if '.' in seat_number:  # 移除可能的小數點部分
                seat_number = seat_number.split('.')[0]
            
            # 如果少於5碼，補0
            if seat_number.isdigit() and len(seat_number) < 5:
                seat_number = seat_number.zfill(5)
            
            # 處理學號格式 (如果有提供)
            if student_id_number:
                student_id_number = str(student_id_number).strip()
                if '.' in student_id_number:  # 移除可能的小數點部分
                    student_id_number = student_id_number.split('.')[0]
                
                # 如果少於6碼，補0
                if student_id_number.isdigit() and len(student_id_number) < 6:
                    student_id_number = student_id_number.zfill(6)
            
            app.logger.debug(f"處理學生資料: 座號={seat_number}, 姓名={name}, 學號={student_id_number}")
            
            # 檢查座號是否已存在
            existing_student = Student.get_by_seat_number(class_id, seat_number)
            
            if existing_student:
                # 更新現有學生
                existing_student.update(
                    name=name,
                    student_id=student_id_number
                )
                app.logger.debug(f"已更新學生: ID={existing_student.id}, 座號={seat_number}")
                updated_count += 1
            else:
                # 創建新學生
                new_student = Student.create(
                    name=name,
                    class_id=class_id,
                    seat_number=seat_number,
                    student_id=student_id_number
                )
                app.logger.debug(f"已創建學生: ID={new_student.id}, 座號={seat_number}")
                created_count += 1
        
        return {
            "success": True,
            "message": f"成功處理學生資料：新增 {created_count} 位，更新 {updated_count} 位",
            "created": created_count,
            "updated": updated_count
        }
    except Exception as e:
        app.logger.error(f"批次管理學生時發生錯誤: {str(e)}")
        return {"success": False, "message": f"處理失敗: {str(e)}"}, 500

@app.route('/api/students/<int:student_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_student(student_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限執行此操作"}, 403
    
    student = Student.get_by_id(student_id)
    if not student:
        return {"success": False, "message": "找不到學生"}, 404
    
    class_obj = Class.get_by_id(student.class_id)
    if not class_obj:
        return {"success": False, "message": "找不到班級"}, 404
    
    if class_obj.teacher_id != current_user.id and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限管理此學生"}, 403
    
    if request.method == 'PUT':
        data = request.json
        name = data.get('name')
        seat_number = data.get('seat_number')
        student_id_value = data.get('student_id', "")
        
        if not name:
            return {"success": False, "message": "學生姓名不能為空"}, 400
        
        # 確保座號是字串格式
        seat_number = str(seat_number).strip()
        if '.' in seat_number:  # 移除可能的小數點部分
            seat_number = seat_number.split('.')[0]
        
        # 檢查座號是否為數字內容
        if not seat_number.isdigit():
            return {"success": False, "message": "座號必須是數字"}, 400
        
        # 如果少於5碼，補0
        if len(seat_number) < 5:
            seat_number = seat_number.zfill(5)
        
        # 處理學號格式 (如果有提供)
        if student_id_value:
            student_id_value = str(student_id_value).strip()
            if '.' in student_id_value:  # 移除可能的小數點部分
                student_id_value = student_id_value.split('.')[0]
            
            # 如果少於6碼，補0
            if student_id_value.isdigit() and len(student_id_value) < 6:
                student_id_value = student_id_value.zfill(6)
        
        # 檢查座號是否已被其他學生使用
        existing_student = Student.get_by_seat_number(student.class_id, seat_number)
        if existing_student and existing_student.id != student.id:
            return {"success": False, "message": f"座號 {seat_number} 已被其他學生使用"}, 400
        
        app.logger.debug(f"更新學生: ID={student.id}, 座號={seat_number}, 姓名={name}, 學號={student_id_value}")
        student.update(name=name, seat_number=seat_number, student_id=student_id_value)
        return {
            "success": True, 
            "message": "學生更新成功", 
            "student": {
                "id": student.id,
                "name": student.name,
                "seat_number": student.seat_number,
                "student_id": student.student_id
            }
        }
    
    elif request.method == 'DELETE':
        if Student.delete(student_id):
            return {"success": True, "message": "學生刪除成功"}
        else:
            return {"success": False, "message": "學生刪除失敗"}, 500

@app.route('/api/classes/<int:class_id>/grade_items', methods=['GET', 'POST'])
@login_required
def manage_class_grade_items(class_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限執行此操作"}, 403
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        return {"success": False, "message": "找不到班級"}, 404
    
    if class_obj.teacher_id != current_user.id and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限管理此班級的成績項目"}, 403
    
    if request.method == 'GET':
        grade_items = GradeItem.get_by_class_id(class_id)
        return {
            "grade_items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "max_score": item.max_score
                } for item in grade_items
            ]
        }
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        max_score = data.get('max_score', 100)
        
        if not name:
            return {"success": False, "message": "成績項目名稱不能為空"}, 400
        
        try:
            max_score = float(max_score)
        except (ValueError, TypeError):
            return {"success": False, "message": "最高分數必須是數字"}, 400
        
        new_item = GradeItem.create(name, class_id, max_score)
        return {
            "success": True, 
            "message": "成績項目創建成功", 
            "grade_item": {
                "id": new_item.id,
                "name": new_item.name,
                "max_score": new_item.max_score
            }
        }

@app.route('/api/grade_items/<int:grade_item_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_grade_item(grade_item_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限執行此操作"}, 403
    
    grade_item = GradeItem.get_by_id(grade_item_id)
    if not grade_item:
        return {"success": False, "message": "找不到成績項目"}, 404
    
    class_obj = Class.get_by_id(grade_item.class_id)
    if not class_obj:
        return {"success": False, "message": "找不到班級"}, 404
    
    if class_obj.teacher_id != current_user.id and current_user.role != 'admin':
        return {"success": False, "message": "您沒有權限管理此成績項目"}, 403
    
    if request.method == 'PUT':
        data = request.json
        name = data.get('name')
        max_score = data.get('max_score')
        
        if not name:
            return {"success": False, "message": "成績項目名稱不能為空"}, 400
        
        try:
            max_score = float(max_score)
        except (ValueError, TypeError):
            return {"success": False, "message": "最高分數必須是數字"}, 400
        
        grade_item.update(name=name, max_score=max_score)
        return {
            "success": True, 
            "message": "成績項目更新成功", 
            "grade_item": {
                "id": grade_item.id,
                "name": grade_item.name,
                "max_score": grade_item.max_score
            }
        }
    
    elif request.method == 'DELETE':
        if GradeItem.delete(grade_item_id):
            return {"success": True, "message": "成績項目刪除成功"}
        else:
            return {"success": False, "message": "成績項目刪除失敗"}, 500

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return render_template('base.html', title='500 - Server Error',
                          error_message='Internal server error. Please try again later.'), 500
