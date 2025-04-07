from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

# 內存數據庫
_users = []
_classes = []
_students = []
_grade_items = []
_grades = []
_access_codes = []
_semesters = ["113-2", "114-1", "114-2"]

class Semester:
    @staticmethod
    def get_all():
        return _semesters
    
    @staticmethod
    def add(semester):
        if semester not in _semesters:
            _semesters.append(semester)
            return True
        return False
    
    @staticmethod
    def remove(semester):
        if semester in _semesters and len(_semesters) > 1:
            _semesters.remove(semester)
            return True
        return False

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, role, student_id=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role  # 'student', 'teacher', or 'admin'
        self.student_id = student_id  # 僅用於學生使用者
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def update(self, username=None, email=None, role=None):
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if role is not None:
            self.role = role
    
    @staticmethod
    def get_by_id(user_id):
        for user in _users:
            if user.id == user_id:
                return user
        return None
    
    @staticmethod
    def get_by_username(username):
        for user in _users:
            if user.username == username:
                return user
        return None
    
    @staticmethod
    def get_all():
        return _users
    
    @staticmethod
    def create(username, email, role, password=None):
        user_id = 1 if not _users else max(user.id for user in _users) + 1
        user = User(user_id, username, email, '', role)
        if password:
            user.set_password(password)
        _users.append(user)
        return user
    
    @staticmethod
    def delete(user_id):
        user = User.get_by_id(user_id)
        if user:
            _users.remove(user)
            return True
        return False

class Class:
    def __init__(self, id, name, teacher_id, semester="113-2"):
        self.id = id
        self.name = name
        self.teacher_id = int(teacher_id) if teacher_id else None
        self.semester = semester
    
    def update(self, name=None, teacher_id=None, semester=None):
        if name is not None:
            self.name = name
        if teacher_id is not None:
            self.teacher_id = int(teacher_id) if teacher_id else None
        if semester is not None:
            self.semester = semester
    
    @staticmethod
    def get_by_id(class_id):
        for cls in _classes:
            if cls.id == class_id:
                return cls
        return None
    
    @staticmethod
    def get_by_teacher_id(teacher_id):
        # 確保 teacher_id 是整數進行比較
        teacher_id = int(teacher_id) if not isinstance(teacher_id, int) else teacher_id
        return [cls for cls in _classes if cls.teacher_id == teacher_id]
    
    @staticmethod
    def get_by_teacher_and_semester(teacher_id, semester):
        # 確保 teacher_id 是整數進行比較
        teacher_id = int(teacher_id) if not isinstance(teacher_id, int) else teacher_id
        return [cls for cls in _classes if cls.teacher_id == teacher_id and cls.semester == semester]
    
    @staticmethod
    def get_all():
        return _classes
    
    @staticmethod
    def create(name, teacher_id, semester="113-2"):
        # 確保 teacher_id 是整數
        teacher_id = int(teacher_id) if teacher_id else None
        
        class_id = 1 if not _classes else max(cls.id for cls in _classes) + 1
        cls = Class(class_id, name, teacher_id, semester)
        _classes.append(cls)
        
        # 記錄創建的班級信息
        print(f"已創建班級: ID={class_id}, 名稱={name}, 教師ID={teacher_id}, 學期={semester}")
        
        return cls
    
    @staticmethod
    def delete(class_id):
        cls = Class.get_by_id(class_id)
        if cls:
            _classes.remove(cls)
            return True
        return False

class Student:
    def __init__(self, id, name, class_id, seat_number="", student_id=""):
        self.id = id
        self.name = name
        self.class_id = int(class_id)
        # 座號始終存儲為字符串，確保一致性
        self.seat_number = str(seat_number) if seat_number else ""  # 座號 (學生登入帳號)
        self.student_id = str(student_id) if student_id else ""     # 學號 (學生登入密碼)
    
    def update(self, name=None, class_id=None, seat_number=None, student_id=None):
        if name is not None:
            self.name = name
        if class_id is not None:
            self.class_id = int(class_id)
        if seat_number is not None:
            self.seat_number = str(seat_number)
        if student_id is not None:
            self.student_id = str(student_id)
    
    @staticmethod
    def get_by_id(student_id):
        for student in _students:
            if student.id == student_id:
                return student
        return None
    
    @staticmethod
    def get_by_seat_number(class_id, seat_number):
        # 確保座號是字符串進行比較
        class_id = int(class_id) if not isinstance(class_id, int) else class_id
        seat_number = str(seat_number) if not isinstance(seat_number, str) else seat_number
        
        for student in _students:
            if student.class_id == class_id and str(student.seat_number) == seat_number:
                return student
        return None
    
    @staticmethod
    def get_by_student_id(student_id_number):
        for student in _students:
            if student.student_id == student_id_number:
                return student
        return None
    
    @staticmethod
    def get_by_class_id(class_id):
        # 確保 class_id 是整數進行比較
        class_id = int(class_id) if not isinstance(class_id, int) else class_id
        return [student for student in _students if student.class_id == class_id]
    
    @staticmethod
    def get_all():
        return _students
    
    @staticmethod
    def create(name, class_id, seat_number="", student_id=""):
        """創建新學生
        
        參數:
            name (str): 學生姓名
            class_id (int): 班級ID
            seat_number (str): 座號 - 5碼數字，作為學生登入帳號
            student_id (str): 學號 - 6碼數字，作為學生登入密碼
        """
        # 確保參數類型正確
        class_id = int(class_id) if not isinstance(class_id, int) else class_id
        seat_number = str(seat_number) if seat_number else ""
        student_id = str(student_id) if student_id else ""
        
        # 格式化座號和學號
        if seat_number:
            # 移除可能的小數點部分
            if "." in seat_number:
                seat_number = seat_number.split(".")[0]
            # 確保座號是5碼數字
            if seat_number.isdigit() and len(seat_number) < 5:
                seat_number = seat_number.zfill(5)
        
        if student_id:
            # 移除可能的小數點部分
            if "." in student_id:
                student_id = student_id.split(".")[0]
            # 確保學號是6碼數字
            if student_id.isdigit() and len(student_id) < 6:
                student_id = student_id.zfill(6)
        
        # 為新學生生成ID
        student_id_int = 1 if not _students else max(student.id for student in _students) + 1
        
        # 創建學生實例
        student = Student(student_id_int, name, class_id, seat_number, student_id)
        _students.append(student)
        
        # 記錄創建的學生信息
        print(f"已創建學生: ID={student_id_int}, 名稱={name}, 班級ID={class_id}, 座號={seat_number}, 學號={student_id}")
        
        return student
    
    @staticmethod
    def get_or_create(name, class_id, seat_number="", student_id=""):
        """獲取或創建學生
        
        首先嘗試查找指定班級中是否有相同座號的學生，
        如果沒有則檢查姓名是否相同，
        如果仍未找到則創建新學生。
        """
        # 確保參數類型正確
        class_id = int(class_id) if not isinstance(class_id, int) else class_id
        seat_number = str(seat_number) if seat_number else ""
        student_id = str(student_id) if student_id else ""
        
        # 格式化座號和學號
        if seat_number:
            # 移除可能的小數點部分
            if "." in seat_number:
                seat_number = seat_number.split(".")[0]
            # 確保座號是5碼數字
            if seat_number.isdigit() and len(seat_number) < 5:
                seat_number = seat_number.zfill(5)
        
        if student_id:
            # 移除可能的小數點部分
            if "." in student_id:
                student_id = student_id.split(".")[0]
            # 確保學號是6碼數字
            if student_id.isdigit() and len(student_id) < 6:
                student_id = student_id.zfill(6)
        
        # 優先使用座號查找學生
        if seat_number:
            student = Student.get_by_seat_number(class_id, seat_number)
            if student:
                # 更新學生資料
                if name and student.name != name:
                    student.name = name
                if student_id and student.student_id != student_id:
                    student.student_id = student_id
                return student
        
        # 如果無法以座號找到，試著以學號查找
        if student_id:
            student = Student.get_by_student_id(student_id)
            if student and student.class_id == class_id:
                # 更新學生資料
                if name and student.name != name:
                    student.name = name
                if seat_number and student.seat_number != seat_number:
                    student.seat_number = seat_number
                return student
        
        # 最後以姓名和班級ID查找
        for student in _students:
            if student.name == name and student.class_id == class_id:
                # 更新學生資料
                if seat_number and student.seat_number != seat_number:
                    student.seat_number = seat_number
                if student_id and student.student_id != student_id:
                    student.student_id = student_id
                return student
        
        # 如果找不到則創建新學生
        return Student.create(name, class_id, seat_number, student_id)
    
    @staticmethod
    def delete(student_id):
        student = Student.get_by_id(student_id)
        if student:
            _students.remove(student)
            return True
        return False

class GradeItem:
    def __init__(self, id, name, class_id, max_score):
        self.id = id
        self.name = name
        self.class_id = int(class_id)
        self.max_score = float(max_score) if max_score else 100.0
    
    def update(self, name=None, class_id=None, max_score=None):
        if name is not None:
            self.name = name
        if class_id is not None:
            self.class_id = int(class_id)
        if max_score is not None:
            self.max_score = float(max_score)
    
    @staticmethod
    def get_by_id(grade_item_id):
        for grade_item in _grade_items:
            if grade_item.id == grade_item_id:
                return grade_item
        return None
    
    @staticmethod
    def get_by_class_id(class_id):
        # 確保 class_id 是整數進行比較
        class_id = int(class_id) if not isinstance(class_id, int) else class_id
        return [grade_item for grade_item in _grade_items if grade_item.class_id == class_id]
    
    @staticmethod
    def get_all():
        return _grade_items
    
    @staticmethod
    def create(name, class_id, max_score):
        grade_item_id = 1 if not _grade_items else max(item.id for item in _grade_items) + 1
        grade_item = GradeItem(grade_item_id, name, class_id, max_score)
        _grade_items.append(grade_item)
        return grade_item
    
    @staticmethod
    def get_or_create(name, class_id, max_score=100):
        # 檢查成績項目是否已存在於班級中
        for grade_item in _grade_items:
            if grade_item.name == name and grade_item.class_id == class_id:
                return grade_item
        
        # 如果找不到則創建新成績項目
        return GradeItem.create(name, class_id, max_score)
    
    @staticmethod
    def delete(grade_item_id):
        grade_item = GradeItem.get_by_id(grade_item_id)
        if grade_item:
            _grade_items.remove(grade_item)
            return True
        return False

class Grade:
    def __init__(self, student_id, grade_item_id, value):
        self.student_id = student_id
        self.grade_item_id = grade_item_id
        self.value = value
    
    @staticmethod
    def get(student_id, grade_item_id):
        for grade in _grades:
            if grade.student_id == student_id and grade.grade_item_id == grade_item_id:
                return grade
        return None
    
    @staticmethod
    def get_by_student_id(student_id):
        return [grade for grade in _grades if grade.student_id == student_id]
    
    @staticmethod
    def get_by_grade_item_id(grade_item_id):
        return [grade for grade in _grades if grade.grade_item_id == grade_item_id]
    
    @staticmethod
    def get_all():
        return _grades
    
    @staticmethod
    def create(student_id, grade_item_id, value):
        # 確保值為數值型別
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = None
        
        grade = Grade(student_id, grade_item_id, value)
        _grades.append(grade)
        return grade
    
    @staticmethod
    def update_or_create(student_id, grade_item_id, value):
        # 確保值為數值型別或 None
        if value and value.strip():
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError("成績必須為數值")
        else:
            value = None
        
        # 驗證成績項目是否存在
        grade_item = GradeItem.get_by_id(grade_item_id)
        if not grade_item:
            raise ValueError("找不到成績項目")
        
        # 驗證學生是否存在
        student = Student.get_by_id(student_id)
        if not student:
            raise ValueError("找不到學生")
        
        # 驗證最高分數
        if value is not None and value > grade_item.max_score:
            raise ValueError(f"成績不能超過最高分數 {grade_item.max_score}")
        
        grade = Grade.get(student_id, grade_item_id)
        if grade:
            grade.value = value
        else:
            grade = Grade.create(student_id, grade_item_id, value)
        
        return grade
    
    @staticmethod
    def delete(student_id, grade_item_id):
        grade = Grade.get(student_id, grade_item_id)
        if grade:
            _grades.remove(grade)
            return True
        return False

class AccessCode:
    def __init__(self, id, code, role, expiry_date=None):
        self.id = id
        self.code = code
        self.role = role  # 'student', 'teacher', or 'admin'
        self.expiry_date = expiry_date
    
    def update(self, code=None, role=None, expiry_date=None):
        if code is not None:
            self.code = code
        if role is not None:
            self.role = role
        if expiry_date is not None:
            self.expiry_date = expiry_date
    
    def is_valid(self):
        if self.expiry_date is None:
            return True
        return datetime.now() < self.expiry_date
    
    @staticmethod
    def get_by_id(access_code_id):
        for access_code in _access_codes:
            if access_code.id == access_code_id:
                return access_code
        return None
    
    @staticmethod
    def get_by_code(code):
        for access_code in _access_codes:
            if access_code.code == code:
                return access_code
        return None
    
    @staticmethod
    def get_all():
        return _access_codes
    
    @staticmethod
    def create(code, role, expiry_date=None):
        access_code_id = 1 if not _access_codes else max(ac.id for ac in _access_codes) + 1
        access_code = AccessCode(access_code_id, code, role, expiry_date)
        _access_codes.append(access_code)
        return access_code
    
    @staticmethod
    def delete(access_code_id):
        access_code = AccessCode.get_by_id(access_code_id)
        if access_code:
            _access_codes.remove(access_code)
            return True
        return False
