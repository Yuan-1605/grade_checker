import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash
import os
import logging

logger = logging.getLogger(__name__)

def initialize_sample_data():
    """初始化應用程式範例資料"""
    from models import User, Class, Student, GradeItem, Grade, AccessCode
    
    # 只在沒有使用者時創建示例資料
    if not User.get_all():
        # 創建教師使用者（根據需求）
        teacher = User.create(
            username="ben",
            email="ben@example.com",
            role="teacher"
        )
        teacher.set_password("1605")
        
        # 創建班級
        class1 = Class.create(
            name="國一甲班",
            teacher_id=teacher.id,
            semester="113-2"
        )
        
        class2 = Class.create(
            name="國一乙班",
            teacher_id=teacher.id,
            semester="113-2"
        )
        
        class3 = Class.create(
            name="國二甲班",
            teacher_id=teacher.id,
            semester="114-1"
        )
        
        # 在沒有已導入學生數據的情況下，創建符合格式要求的示例學生
        # 座號必須為五碼數字，學號必須為六碼數字
        if not Student.get_all():
            logger.info("創建示例學生數據...")
            
            # 班級1 - 國一甲班
            student1 = Student.create(
                name="張小明",
                class_id=class1.id,
                seat_number="30102",
                student_id="111230"
            )
            
            student2 = Student.create(
                name="王小華",
                class_id=class1.id,
                seat_number="30105", 
                student_id="111250"
            )
            
            student3 = Student.create(
                name="李小強",
                class_id=class1.id,
                seat_number="30109",
                student_id="111290"
            )
            
            # 班級2 - 國一乙班
            student4 = Student.create(
                name="陳小美",
                class_id=class2.id,
                seat_number="40101",
                student_id="111304"
            )
            
            student5 = Student.create(
                name="林小玲",
                class_id=class2.id,
                seat_number="40105",
                student_id="111350"
            )
            
            # 班級3 - 國二甲班
            student6 = Student.create(
                name="黃小龍",
                class_id=class3.id,
                seat_number="50101",
                student_id="121106"
            )
        
        # 創建成績項目（如果尚未有成績項目）
        if not GradeItem.get_all():
            logger.info("創建示例成績項目...")
            
            # 國一甲班成績項目
            exam1 = GradeItem.create(
                name="第一次月考",
                class_id=class1.id,
                max_score=100
            )
            
            exam2 = GradeItem.create(
                name="第二次月考",
                class_id=class1.id,
                max_score=100
            )
            
            homework = GradeItem.create(
                name="平時作業",
                class_id=class1.id,
                max_score=50
            )
            
            # 國一乙班成績項目
            exam1_b = GradeItem.create(
                name="第一次月考",
                class_id=class2.id,
                max_score=100
            )
            
            exam2_b = GradeItem.create(
                name="第二次月考",
                class_id=class2.id,
                max_score=100
            )
            
            # 如果已有學生，但沒有成績，添加示例成績
            if not Grade.get_all():
                logger.info("創建示例成績...")
                
                # 獲取學生資料
                students = Student.get_all()
                if students:
                    # 國一甲班學生成績
                    class1_students = [s for s in students if s.class_id == class1.id]
                    for i, student in enumerate(class1_students[:3]):
                        # 第一次月考成績 (75-85分)
                        Grade.create(
                            student_id=student.id,
                            grade_item_id=exam1.id,
                            value=75 + (i * 5)
                        )
                        
                        # 第二次月考成績 (80-90分)
                        Grade.create(
                            student_id=student.id,
                            grade_item_id=exam2.id,
                            value=80 + (i * 5)
                        )
                        
                        # 平時作業成績 (40-45分)
                        Grade.create(
                            student_id=student.id,
                            grade_item_id=homework.id,
                            value=40 + i
                        )
                    
                    # 國一乙班學生成績
                    class2_students = [s for s in students if s.class_id == class2.id]
                    for i, student in enumerate(class2_students[:2]):
                        # 第一次月考成績 (70-80分)
                        Grade.create(
                            student_id=student.id,
                            grade_item_id=exam1_b.id,
                            value=70 + (i * 10)
                        )
                        
                        # 第二次月考成績 (75-85分)
                        Grade.create(
                            student_id=student.id,
                            grade_item_id=exam2_b.id,
                            value=75 + (i * 10)
                        )
        
        # 創建訪問碼（如果尚未有訪問碼）
        if not AccessCode.get_all():
            logger.info("創建訪問碼...")
            
            AccessCode.create(
                code="STUDENT2023",
                role="student"
            )
            
            AccessCode.create(
                code="TEACHER2023",
                role="teacher"
            )
            
            AccessCode.create(
                code="ADMIN2023",
                role="admin"
            )
        
        logger.info("示例資料初始化完成")

def allowed_file(filename):
    """Check if a file is an allowed Excel file."""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_excel_file(file, class_id):
    """處理 Excel 檔案並匯入成績。
    
    預期檔案結構:
    - 第一列為標題列，包含: '姓名', '座號', '學號', 以及各成績項目名稱
    - 後續各列為學生資料和成績
    """
    from models import Student, GradeItem, Grade
    
    # 載入 Excel 檔案
    try:
        df = pd.read_excel(file)
        logger.info(f"Excel 檔案欄位: {df.columns.tolist()}")
    except Exception as e:
        logger.error(f"讀取 Excel 檔案錯誤: {str(e)}")
        raise ValueError(f"無法讀取 Excel 檔案: {str(e)}")
    
    # 驗證檔案結構
    required_columns = ['姓名']
    optional_columns = ['座號', '學號']
    
    # 檢查是否至少有 '姓名' 欄位
    found_name_column = False
    for col in df.columns:
        if col in ['姓名', 'name', '學生姓名', '學生', 'student name', 'student_name', 'student']:
            found_name_column = True
            break
    
    if not found_name_column:
        raise ValueError("Excel 檔案必須包含姓名欄位 (標示為 '姓名', 'Name', '學生姓名', 等)")
    
    # 建立計數器追蹤創建的項目
    results = {
        "students_created": 0,
        "grade_items_created": 0,
        "grades_imported": 0
    }
    
    # 識別姓名、座號、學號欄位
    name_col = None
    seat_col = None
    student_id_col = None
    
    for col in df.columns:
        if col.lower() in ['姓名', 'name', '學生姓名', '學生', 'student name', 'student_name', 'student']:
            name_col = col
        elif col.lower() in ['座號', 'seat number', 'seat', 'seat_number']:
            seat_col = col
        elif col.lower() in ['學號', 'student id', 'student_id', 'id']:
            student_id_col = col
    
    if not name_col:
        raise ValueError("找不到姓名欄位")
    
    logger.info(f"使用欄位 - 姓名: {name_col}, 座號: {seat_col}, 學號: {student_id_col}")
    
    # 處理每一列(學生)
    for idx, row in df.iterrows():
        student_name = row[name_col]
        
        # 跳過空名稱
        if not student_name or pd.isna(student_name):
            continue
        
        # 獲取座號和學號(如果有)
        seat_number = ""
        student_id_number = ""
        
        if seat_col and not pd.isna(row[seat_col]):
            # 確保座號是字串且格式正確(5碼數字)
            try:
                seat_val = str(row[seat_col]).strip()
                # 如果是數值，可能被 Excel 讀取為浮點數
                if '.' in seat_val:
                    seat_val = seat_val.split('.')[0]
                
                # 確保座號格式正確
                if len(seat_val) > 0:
                    # 如果少於5碼，補0
                    if len(seat_val) < 5:
                        seat_val = seat_val.zfill(5)
                    seat_number = seat_val
            except:
                seat_number = ""
        
        if student_id_col and not pd.isna(row[student_id_col]):
            # 確保學號是字串且格式正確(6碼數字)
            try:
                id_val = str(row[student_id_col]).strip()
                # 如果是數值，可能被 Excel 讀取為浮點數
                if '.' in id_val:
                    id_val = id_val.split('.')[0]
                
                # 確保學號格式正確
                if len(id_val) > 0:
                    # 如果少於6碼，補0
                    if len(id_val) < 6:
                        id_val = id_val.zfill(6)
                    student_id_number = id_val
            except:
                student_id_number = ""
        
        logger.info(f"處理學生: {student_name}, 座號: {seat_number}, 學號: {student_id_number}")
        
        # 先嘗試以座號查找學生
        student = None
        if seat_number:
            student = Student.get_by_seat_number(int(class_id), seat_number)
        
        # 如果沒找到且有學號，以學號查找
        if not student and student_id_number:
            student = Student.get_by_student_id(student_id_number)
        
        # 如果仍未找到，建立新學生
        if not student:
            student = Student.create(
                name=student_name,
                class_id=int(class_id),
                seat_number=seat_number,
                student_id=student_id_number
            )
            results["students_created"] += 1
            logger.info(f"創建新學生: {student_name}, ID: {student.id}")
        
        # 處理成績項目
        grade_columns = [col for col in df.columns if col not in [name_col, seat_col, student_id_col]]
        
        for col_name in grade_columns:
            if pd.isna(col_name) or not col_name:
                continue
            
            # 建立或獲取成績項目
            grade_item = GradeItem.get_or_create(name=col_name, class_id=int(class_id))
            if grade_item.id not in [gi.id for gi in GradeItem.get_all()]:
                results["grade_items_created"] += 1
                logger.info(f"創建新成績項目: {col_name}, ID: {grade_item.id}")
            
            # 設定成績值
            grade_value = row[col_name]
            if not pd.isna(grade_value):
                try:
                    # 確保成績是數值
                    numeric_value = float(grade_value)
                    Grade.update_or_create(
                        student_id=student.id,
                        grade_item_id=grade_item.id,
                        value=numeric_value
                    )
                    results["grades_imported"] += 1
                except Exception as e:
                    logger.warning(f"無法匯入成績 - 學生: {student_name}, 項目: {col_name}, 錯誤: {str(e)}")
    
    return results

def get_student_grades(student_id):
    """Get all grades for a student with associated details."""
    from models import Student, GradeItem, Grade, Class
    
    student = Student.get_by_id(student_id)
    if not student:
        return []
    
    grades_data = []
    class_obj = Class.get_by_id(student.class_id)
    grade_items = GradeItem.get_by_class_id(student.class_id)
    
    for grade_item in grade_items:
        grade = Grade.get(student_id, grade_item.id)
        
        grades_data.append({
            'class_name': class_obj.name if class_obj else 'Unknown Class',
            'grade_item_name': grade_item.name,
            'max_score': grade_item.max_score,
            'value': grade.value if grade else None,
            'percentage': (grade.value / grade_item.max_score * 100) if grade and grade.value is not None else None
        })
    
    return grades_data

def get_classes_for_teacher(teacher_id):
    """Get all classes taught by a teacher."""
    from models import Class
    
    return Class.get_by_teacher_id(teacher_id)
