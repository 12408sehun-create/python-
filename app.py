"""
大学生管理系统 - Flask后端
"""
# 端口 1122
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'college_management_secret_key'

# 清除flash消息的处理器
@app.after_request
def clear_flash_messages(response):
    """每次请求后清除flash消息，防止重复显示"""
    if '_flashes' in session:
        # 保留flash消息用于显示，但确保它们只显示一次
        # Flask的get_flashed_messages已经会自动清除，所以这里不需要额外处理
        pass
    return response

# 固定专业列表
MAJORS = ['中文系', '英文系']

# 在 Jinja2 中添加全局变量 - 从 session 获取登录类型
@app.context_processor
def inject_login_type():
    try:
        login_type = session.get('login_type')
        username = session.get('username')
        user_id = session.get('user_id')
    except RuntimeError:
        # Session is not available
        login_type = None
        username = None
        user_id = None
    return dict(current_login_type=login_type, current_username=username, current_user_id=user_id)

# 手机号脱敏过滤器
@app.template_filter('mask_phone')
def mask_phone(phone):
    """将手机号最后两位替换为**"""
    if not phone or len(phone) < 2:
        return phone
    return phone[:-2] + '**'

# 数据库初始化
def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    
    # 学生表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            major TEXT NOT NULL,
            class_name TEXT NOT NULL,
            grade_year INTEGER,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 课程表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            teacher TEXT,
            semester TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # 成绩表 - course_id 可为空用于批量添加
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER,
            score REAL,
            semester TEXT NOT NULL,
            exam_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')
    
    # 考勤表 - course_id 可为空用于批量添加
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            remarks TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')
    
    # 班级表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            major TEXT NOT NULL,
            grade_year INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 新闻表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# 数据库迁移 - 确保表结构正确（只添加缺失的列，不重建表）
def migrate_db():
    """数据库迁移 - 只添加缺失的列"""
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    
    # 检查并添加 students.grade_year
    try:
        cursor.execute('SELECT grade_year FROM students LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE students ADD COLUMN grade_year INTEGER')
    
    # 检查并添加 classes.major
    try:
        cursor.execute('SELECT major FROM classes LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE classes ADD COLUMN major TEXT')
    
    # 检查并添加 classes.created_at
    try:
        cursor.execute('SELECT created_at FROM classes LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE classes ADD COLUMN created_at TEXT')
    
    # 检查并添加 classes.updated_at
    try:
        cursor.execute('SELECT updated_at FROM classes LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE classes ADD COLUMN updated_at TEXT')
    
    # 检查并添加 students.enrollment_date
    try:
        cursor.execute('SELECT enrollment_date FROM students LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE students ADD COLUMN enrollment_date TEXT')
        cursor.execute('ALTER TABLE students ADD COLUMN months_paid INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE students ADD COLUMN last_payment_date TEXT')
    
    # 检查并添加 grades.course_name
    try:
        cursor.execute('SELECT course_name FROM grades LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE grades ADD COLUMN course_name TEXT')
    
    # 检查并添加 attendance.course_name
    try:
        cursor.execute('SELECT course_name FROM attendance LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE attendance ADD COLUMN course_name TEXT')
    
    # 检查并添加 grades.updated_at
    try:
        cursor.execute('SELECT updated_at FROM grades LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE grades ADD COLUMN updated_at TEXT')
    
    # 检查并添加 attendance.updated_at
    try:
        cursor.execute('SELECT updated_at FROM attendance LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE attendance ADD COLUMN updated_at TEXT')
    
    # 检查并添加 news.updated_at
    try:
        cursor.execute('SELECT updated_at FROM news LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE news ADD COLUMN updated_at TEXT')
    
    # 检查并添加 students.graduation_status
    try:
        cursor.execute('SELECT graduation_status FROM students LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE students ADD COLUMN graduation_status TEXT DEFAULT "在校"')
    
    # 检查并添加 classes.is_graduated
    try:
        cursor.execute('SELECT is_graduated FROM classes LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE classes ADD COLUMN is_graduated INTEGER DEFAULT 0')
    

    # 检查并添加 grades.attendance_score (出勤成绩)
    try:
        cursor.execute('SELECT attendance_score FROM grades LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE grades ADD COLUMN attendance_score REAL')

    # 检查并添加 grades.activity_score (活动成绩)
    try:
        cursor.execute('SELECT activity_score FROM grades LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE grades ADD COLUMN activity_score REAL')

    # 检查并添加 grades.final_score (期末成绩)
    try:
        cursor.execute('SELECT final_score FROM grades LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE grades ADD COLUMN final_score REAL')
    
    conn.commit()
    conn.close()
    # 初始化数据库
    init_db()
    migrate_db()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('college.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_page_for_student(student_id, search_query, major_filter, class_filter, per_page=15):
    """计算学生应该在哪一页"""
    conn = get_db_connection()
    
    # 构建查询条件
    conditions = []
    params = []

    if search_query:
        conditions.append('(name LIKE ? OR student_id LIKE ? OR class_name LIKE ?)')
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if major_filter:
        conditions.append('major = ?')
        params.append(major_filter)
    if class_filter:
        conditions.append('class_name = ?')
        params.append(class_filter)

    # 核心修复：使用 CAST 转换为数值比较，与 index 路由的排序规则保持绝对一致
    position_query = 'SELECT COUNT(*) as position FROM students WHERE CAST(student_id AS INTEGER) < CAST(? AS INTEGER)'
    position_params = [student_id]

    if conditions:
        position_query += ' AND ' + ' AND '.join(conditions)
        position_params.extend(params)
    
    result = conn.execute(position_query, position_params).fetchone()
    position = result['position'] + 1 if result else 1
    
    # 计算页码
    page = (position - 1) // per_page + 1
    
    conn.close()
    return page


    # if search_query:
    #     query = '''
    #         SELECT COUNT(*) as position
    #         FROM students 
    #         WHERE (name LIKE ? OR student_id LIKE ? OR class_name LIKE ?)
    #         AND (major, grade_year, class_name, name) <= (
    #             SELECT major, grade_year, class_name, name 
    #             FROM students 
    #             WHERE id = ?
    #         )
    #     '''
    #     params = (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', student_id)
    # elif major_filter:
    #     query = '''
    #         SELECT COUNT(*) as position
    #         FROM students 
    #         WHERE major = ?
    #         AND (grade_year, class_name, name) <= (
    #             SELECT grade_year, class_name, name 
    #             FROM students 
    #             WHERE id = ?
    #         )
    #     '''
    #     params = (major_filter, student_id)
    # elif class_filter:
    #     query = '''
    #         SELECT COUNT(*) as position
    #         FROM students 
    #         WHERE class_name = ?
    #         AND (major, grade_year, class_name, name) <= (
    #             SELECT major, grade_year, class_name, name 
    #             FROM students 
    #             WHERE id = ?
    #         )
    #     '''
    #     params = (class_filter, student_id)
    # else:
    #     query = '''
    #         SELECT COUNT(*) as position
    #         FROM students 
    #         WHERE (major, grade_year, class_name, name) <= (
    #             SELECT major, grade_year, class_name, name 
    #             FROM students 
    #             WHERE id = ?
    #         )
    #     '''
    #     params = (student_id,)
    
    # result = conn.execute(query, params).fetchone()
    # position = result['position'] if result else 1
    
    # # 计算页码
    # page = (position - 1) // per_page + 1
    
    # conn.close()
    # return page

# ==================== 学生管理 ====================

@app.route('/students')
def index():
    """学生列表页面"""
    search_query = request.args.get('search', '')
    major_filter = request.args.get('major', '')
    class_filter = request.args.get('class', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 构建基础查询和计数查询
    if search_query:
        base_query = '''
            SELECT * FROM students 
            WHERE name LIKE ? OR student_id LIKE ? OR class_name LIKE ?
        '''
        params = (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')
        count_query = '''
            SELECT COUNT(*) FROM students 
            WHERE name LIKE ? OR student_id LIKE ? OR class_name LIKE ?
        '''
        count_params = params
    elif major_filter:
        base_query = '''
            SELECT * FROM students 
            WHERE major = ?
        '''
        params = (major_filter,)
        count_query = 'SELECT COUNT(*) FROM students WHERE major = ?'
        count_params = params
    elif class_filter:
        base_query = '''
            SELECT * FROM students 
            WHERE class_name = ?
        '''
        params = (class_filter,)
        count_query = 'SELECT COUNT(*) FROM students WHERE class_name = ?'
        count_params = params
    else:
        base_query = 'SELECT * FROM students'
        params = ()
        count_query = 'SELECT COUNT(*) FROM students'
        count_params = ()
    
    # 添加排序
    base_query += ' ORDER BY CAST(student_id AS INTEGER) ASC'
    
    # 获取总记录数
    total = conn.execute(count_query, count_params).fetchone()[0]
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 获取当前页数据
    offset = (page - 1) * per_page
    if params:
        students = conn.execute(base_query + ' LIMIT ? OFFSET ?', params + (per_page, offset)).fetchall()
    else:
        students = conn.execute(base_query + ' LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    
    # 获取所有班级用于筛选
    all_classes = conn.execute('SELECT DISTINCT class_name FROM classes ORDER BY class_name').fetchall()
    
    conn.close()
    
    # 从Session获取高亮学生，然后清除Session中的高亮状态
    highlighted_student = session.get('highlighted_student')
    if highlighted_student:
        session.pop('highlighted_student', None)
    
    return render_template('index.html', students=students, search_query=search_query, 
                         major_filter=major_filter, class_filter=class_filter,
                         all_classes=all_classes,
                         highlighted_student=highlighted_student, 
                         page=page, total_pages=total_pages, total=total)

@app.route('/add', methods=('GET', 'POST'))
def add_student():
    """添加学生"""
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        gender = request.form['gender']
        age = int(request.form['age'])
        major = request.form['major']
        class_name = request.form['class_name']
        grade_year = request.form.get('grade_year')
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        enrollment_date = request.form.get('enrollment_date', '')
        months_paid = int(request.form.get('months_paid', 0))
        graduation_status = request.form.get('graduation_status', '在校')
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO students (student_id, name, gender, age, major, class_name, grade_year, phone, email, address, enrollment_date, months_paid, graduation_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, name, gender, age, major, class_name, grade_year, phone, email, address, enrollment_date, months_paid, graduation_status, now, now))
            conn.commit()
            
            # 获取刚插入的学生ID
            student = conn.execute('SELECT id FROM students WHERE student_id = ?', (student_id,)).fetchone()
            student_id_value = student['id'] if student else None
            
            flash('学生添加成功！', 'success')
            
            # 清除之前的高亮状态，只高亮最近添加的学生
            if student_id_value:
                session['highlighted_student'] = student_id_value
            session.pop('highlighted_class', None)
            session.pop('highlighted_grade', None)
            session.pop('highlighted_attendance', None)
            
            # 计算学生应该在哪一页
            page = calculate_page_for_student(student_id, '', '', '')
            
            # 跳转到正确的页面
            return redirect(url_for('index', page=page))
        except sqlite3.IntegrityError:
            flash('学号已存在，请使用不同的学号！', 'error')
        finally:
            conn.close()
    
    return render_template('add.html', majors=MAJORS)

@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_student(id):
    """编辑学生"""
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        gender = request.form['gender']
        age = int(request.form['age'])
        major = request.form['major']
        class_name = request.form['class_name']
        grade_year = request.form.get('grade_year')
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        enrollment_date = request.form.get('enrollment_date', '')
        months_paid = int(request.form.get('months_paid', 0))
        graduation_status = request.form.get('graduation_status', '在校')
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            conn.execute('''
                UPDATE students 
                SET student_id=?, name=?, gender=?, age=?, major=?, class_name=?, grade_year=?, phone=?, email=?, address=?, enrollment_date=?, months_paid=?, graduation_status=?, updated_at=?
                WHERE id=?
            ''', (student_id, name, gender, age, major, class_name, grade_year, phone, email, address, enrollment_date, months_paid, graduation_status, now, id))
            conn.commit()
            flash('学生信息更新成功！', 'success')
            
            # 清除之前的高亮状态，只高亮最近修改的学生
            session['highlighted_student'] = id
            session.pop('highlighted_class', None)
            session.pop('highlighted_grade', None)
            session.pop('highlighted_attendance', None)
            
            # 计算学生应该在哪一页
            page = calculate_page_for_student(student_id, '', '', '')
            
            # 跳转到正确的页面
            return redirect(url_for('index', page=page))
        except sqlite3.IntegrityError:
            flash('学号已存在，请使用不同的学号！', 'error')
        finally:
            conn.close()
    
    conn.close()
    return render_template('edit.html', student=student, majors=MAJORS)

@app.route('/delete/<int:id>', methods=('POST',))
def delete_student(id):
    """删除学生"""
    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('学生删除成功！', 'success')
    return redirect(url_for('index'))

@app.route('/view/<int:id>')
def view_student(id):
    """查看学生详情"""
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    
    conn.close()
    return render_template('view.html', student=student)

# ==================== 成绩管理 ====================

@app.route('/grades')
def grades():
    """成绩列表"""
    student_filter = request.args.get('student', '')
    class_filter = request.args.get('class', '')
    semester_filter = request.args.get('semester', '')
    major_filter = request.args.get('major', '')
    exam_date_filter = request.args.get('exam_date', '')
    just_added = request.args.get('just_added', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 如果有考试日期筛选，显示该日期的所有记录；否则只显示每个学生的最新记录
    if exam_date_filter:
        query = '''
            SELECT g.*, s.name as student_name, s.student_id, s.class_name
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            WHERE g.exam_date = ?
        '''
        params = [exam_date_filter]
        
        if student_filter:
            query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
            params.extend([f'%{student_filter}%', f'%{student_filter}%'])
        if class_filter:
            query += ' AND s.class_name = ?'
            params.append(class_filter)
        if semester_filter:
            query += ' AND g.semester = ?'
            params.append(semester_filter)
        if major_filter:
            query += ' AND s.major = ?'
            params.append(major_filter)
        
        query += ' ORDER BY s.name'
        count_query = query.replace('SELECT g.*, s.name as student_name, s.student_id, s.class_name', 'SELECT COUNT(*)')
    else:
        query = '''
            SELECT g.*, s.name as student_name, s.student_id, s.class_name
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            WHERE g.id IN (
                SELECT MAX(id) FROM grades GROUP BY student_id
            )
        '''
        params = []
        
        if student_filter:
            query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
            params.extend([f'%{student_filter}%', f'%{student_filter}%'])
        if class_filter:
            query += ' AND s.class_name = ?'
            params.append(class_filter)
        if semester_filter:
            query += ' AND g.semester = ?'
            params.append(semester_filter)
        if major_filter:
            query += ' AND s.major = ?'
            params.append(major_filter)
        
        query += ' ORDER BY g.created_at DESC, s.name'
        # 计数查询需要特殊处理
        count_query = '''
            SELECT COUNT(*) FROM grades g
            JOIN students s ON g.student_id = s.student_id
            WHERE g.id IN (
                SELECT MAX(id) FROM grades GROUP BY student_id
            )
        '''
        count_params = []
        if student_filter:
            count_query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
            count_params.extend([f'%{student_filter}%', f'%{student_filter}%'])
        if class_filter:
            count_query += ' AND s.class_name = ?'
            count_params.append(class_filter)
        if semester_filter:
            count_query += ' AND g.semester = ?'
            count_params.append(semester_filter)
        if major_filter:
            count_query += ' AND s.major = ?'
            count_params.append(major_filter)
    
    # 获取总记录数
    if exam_date_filter:
        total = conn.execute(count_query, params).fetchone()[0]
    else:
        total = conn.execute(count_query, count_params).fetchone()[0]
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 获取当前页数据
    offset = (page - 1) * per_page
    query_params = tuple(params) + (per_page, offset)
    grades = conn.execute(query + ' LIMIT ? OFFSET ?', query_params).fetchall()
    
    # 获取所有班级用于筛选 - 从班级表获取
    all_classes = conn.execute('SELECT DISTINCT class_name FROM classes ORDER BY class_name').fetchall()
    
    conn.close()
    
    # 从Session获取高亮成绩，然后清除Session中的高亮状态
    highlighted_grade = session.get('highlighted_grade')
    if highlighted_grade:
        session.pop('highlighted_grade', None)
    
    return render_template('grades.html', grades=grades, all_classes=all_classes,
                          student_filter=student_filter, class_filter=class_filter, 
                          semester_filter=semester_filter, major_filter=major_filter,
                          exam_date_filter=exam_date_filter, just_added=just_added,
                          highlighted_grade=highlighted_grade,
                          has_filter=True, page=page, total_pages=total_pages, total=total)

# 成绩详情页
@app.route('/grades/detail/<student_id>')
def grade_detail(student_id):
    """成绩详情 - 显示某学生的所有成绩"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    highlight_id = request.args.get('highlight_id', type=int)
    from_view = request.args.get('from_view', '')
    
    # 获取学生信息
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
    
    # 获取成绩总数
    total = conn.execute('SELECT COUNT(*) FROM grades WHERE student_id = ?', (student_id,)).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 获取成绩（带分页）
    offset = (page - 1) * per_page
    all_grades = conn.execute('''
        SELECT * FROM grades 
        WHERE student_id = ?
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
    ''', (student_id, per_page, offset)).fetchall()
    conn.close()
    return render_template('grade_detail.html', student=student, grades=all_grades, highlight_id=highlight_id,
                         page=page, total_pages=total_pages, total=total, from_view=from_view)

@app.route('/grades/add', methods=('GET', 'POST'))
def add_grade():
    """添加成绩"""
    conn = get_db_connection()
    
    # 获取所有班级
    classes = conn.execute('SELECT * FROM classes ORDER BY grade_year DESC, class_name').fetchall()
    
    # 获取所有学生
    all_students = conn.execute('SELECT student_id, name, class_name FROM students ORDER BY class_name, name').fetchall()
    
    students = []
    selected_class = None
    
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        semester = request.form['semester']
        exam_date = request.form['exam_date']
        course_name = request.form.get('course_name', '')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 批量添加成绩
        success_count = 0
        skipped_count = 0
        
        if class_name:
            # 获取该班级的学生
            students_to_add = conn.execute('SELECT student_id FROM students WHERE class_name = ?', (class_name,)).fetchall()
            
            # 记录成功添加的学生ID列表（用于高亮显示）
            added_student_ids = []
            
            for student in students_to_add:
                student_id = student['student_id']
                score_key = f'score_{student_id}'
                score = request.form.get(score_key)

                attendance_score = request.form.get(f'attendance_score_{student_id}')
                activity_score = request.form.get(f'activity_score_{student_id}')
                final_score = request.form.get(f'final_score_{student_id}')


                 # 只要填写了任意一项成绩就插入数据库
                has_any_score = (score and score.strip()) or (attendance_score and attendance_score.strip()) or (activity_score and activity_score.strip()) or (final_score and final_score.strip())
                if has_any_score:
                    try:
                        score_float = float(score) if score and score.strip() else None

                # 只有填写了成绩的学生才插入数据库，未填成绩视为未参加考试
                # if score and score.strip():
                #     try:
                #         score_float = float(score)

                        # 如果前端没填，默认存入 None
                        att_float = float(attendance_score) if attendance_score and attendance_score.strip() else None
                        act_float = float(activity_score) if activity_score and activity_score.strip() else None
                        fin_float = float(final_score) if final_score and final_score.strip() else None

                        conn.execute('''
                            INSERT INTO grades (student_id, score, semester, exam_date, course_name, attendance_score, activity_score, final_score, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (student_id, score_float, semester, exam_date, course_name, att_float, act_float, fin_float, now, now))
                        success_count += 1
                        added_student_ids.append(student_id)
                    except Exception:
                        pass
                else:
                    # 未填成绩的学生数量
                    skipped_count += 1
        
        conn.commit()
        flash(f'成功添加 {success_count} 条成绩记录' + (f'，跳过 {skipped_count} 条未填写成绩' if skipped_count > 0 else ''), 'success')
        
        # 清除之前的高亮状态，只高亮最近添加的成绩
        if added_student_ids:
            session['highlighted_grade'] = ','.join(added_student_ids)
        session.pop('highlighted_class', None)
        session.pop('highlighted_attendance', None)
        
        # 跳转到列表主页第一页，显示每个学生的最新记录，并高亮刚添加的学生
        return redirect(url_for('grades', page=1))
    
    conn.close()
    return render_template('grade_add.html', students=students, classes=classes, selected_class=selected_class, all_students=all_students)


@app.route('/grades/batch_edit', methods=('POST',))  # 确保只接收POST请求
def batch_edit_grades():
    """批量修改成绩"""
    major = request.form.get('major')
    class_name = request.form.get('class_name')
    semester = request.form.get('semester', '').strip()
    exam_date = request.form.get('exam_date', '').strip()
    course_name = request.form.get('course_name', '').strip()
    
    if not major or not class_name:
        flash('必须选择专业和班级进行筛选！', 'error')
        return redirect(url_for('grades'))
        
    conn = get_db_connection()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 动态构建UPDATE语句
    updates = []
    params = []
    if semester:
        updates.append("semester = ?")
        params.append(semester)
    if exam_date:
        updates.append("exam_date = ?")
        params.append(exam_date)
    if course_name:
        updates.append("course_name = ?")
        params.append(course_name)
        
    if not updates:
        conn.close()
        flash('未填写任何需要修改的内容！', 'error')
        return redirect(url_for('grades'))
        
    updates.append("updated_at = ?")
    params.append(now)
    
    # 通过子查询关联学生表匹配专业和班级
    query = '''
        UPDATE grades 
        SET {} 
        WHERE student_id IN (
            SELECT student_id FROM students WHERE major = ? AND class_name = ?
        )
    '''.format(', '.join(updates))
    
    params.extend([major, class_name])
    
    try:
        conn.execute(query, tuple(params))
        conn.commit()
        flash('成绩批量修改成功！', 'success')
    except Exception as e:
        flash(f'批量修改失败：{e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('grades'))





@app.route('/grades/edit/<int:id>', methods=('GET', 'POST'))
def edit_grade(id):
    """编辑成绩"""
    conn = get_db_connection()
    grade = conn.execute('''
        SELECT g.*, s.name as student_name, c.course_name
        FROM grades g
        JOIN students s ON g.student_id = s.student_id
        LEFT JOIN courses c ON g.course_id = c.id
        WHERE g.id = ?
    ''', (id,)).fetchone()
    student_id = grade['student_id']
    
    if request.method == 'POST':
        score = float(request.form.get('score')) if request.form.get('score') else None
        exam_date = request.form['exam_date']
        semester = request.form.get('semester', '').strip()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
         # 获取出勤、活动、期末成绩，未填写则存入 None
        attendance_score = float(request.form['attendance_score']) if request.form.get('attendance_score') else None
        activity_score = float(request.form['activity_score']) if request.form.get('activity_score') else None
        final_score = float(request.form['final_score']) if request.form.get('final_score') else None
        
        conn.execute('''
            UPDATE grades SET score = ?, attendance_score = ?, activity_score = ?, final_score = ?, semester = ?, exam_date = ?, updated_at = ? WHERE id = ?
        ''', (score, attendance_score, activity_score, final_score, semester, exam_date, now, id))
        conn.commit()
        conn.close()
        flash('成绩更新成功！', 'success')
        # 回到成绩详情页并高亮显示刚修改的记录
        return redirect(url_for('grade_detail', student_id=student_id, highlight_id=id))
    
    conn.close()
    return render_template('grade_edit.html', grade=grade)

@app.route('/grades/delete/<int:id>', methods=('POST',))
def delete_grade(id):
    """删除成绩"""
    conn = get_db_connection()
    # 先获取该成绩记录对应的学生ID，以便删除后返回详情页
    grade = conn.execute('SELECT student_id FROM grades WHERE id = ?', (id,)).fetchone()
    student_id = grade['student_id'] if grade else None
    conn.execute('DELETE FROM grades WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('成绩删除成功！', 'success')
    # 返回成绩详情页
    if student_id:
        return redirect(url_for('grade_detail', student_id=student_id))
    return redirect(url_for('grades'))

# ==================== 考勤管理 ====================

@app.route('/attendance')
def attendance():
    """考勤列表"""
    student_filter = request.args.get('student', '')
    class_filter = request.args.get('class', '')
    status_filter = request.args.get('status', '')
    major_filter = request.args.get('major', '')
    date_filter = request.args.get('date', '')
    just_added = request.args.get('just_added', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 如果有日期筛选，显示该日期的所有记录；否则只显示每个学生的最新记录
    if date_filter:
        query = '''
            SELECT a.*, s.name as student_name, s.student_id, s.class_name
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date = ?
        '''
        params = [date_filter]
        
        if student_filter:
            query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
            params.extend([f'%{student_filter}%', f'%{student_filter}%'])
        if class_filter:
            query += ' AND s.class_name = ?'
            params.append(class_filter)
        if status_filter:
            query += ' AND a.status = ?'
            params.append(status_filter)
        if major_filter:
            query += ' AND s.major = ?'
            params.append(major_filter)
        
        query += ' ORDER BY s.name'
        count_query = query.replace('SELECT a.*, s.name as student_name, s.student_id, s.class_name', 'SELECT COUNT(*)')
    else:
        query = '''
            SELECT a.*, s.name as student_name, s.student_id, s.class_name
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.id IN (
                SELECT MAX(id) FROM attendance GROUP BY student_id
            )
        '''
        params = []
        
        if student_filter:
            query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
            params.extend([f'%{student_filter}%', f'%{student_filter}%'])
        if class_filter:
            query += ' AND s.class_name = ?'
            params.append(class_filter)
        if status_filter:
            query += ' AND a.status = ?'
            params.append(status_filter)
        if major_filter:
            query += ' AND s.major = ?'
            params.append(major_filter)
        
        query += ' ORDER BY a.created_at DESC, s.name'
        count_query = '''
            SELECT COUNT(*) FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.id IN (
                SELECT MAX(id) FROM attendance GROUP BY student_id
            )
        '''
        count_params = []
        if student_filter:
            count_query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
            count_params.extend([f'%{student_filter}%', f'%{student_filter}%'])
        if class_filter:
            count_query += ' AND s.class_name = ?'
            count_params.append(class_filter)
        if status_filter:
            count_query += ' AND a.status = ?'
            count_params.append(status_filter)
        if major_filter:
            count_query += ' AND s.major = ?'
            count_params.append(major_filter)
    
    # 获取总记录数
    if date_filter:
        total = conn.execute(count_query, params).fetchone()[0]
    else:
        total = conn.execute(count_query, count_params).fetchone()[0]
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 获取当前页数据
    offset = (page - 1) * per_page
    query_params = tuple(params) + (per_page, offset)
    records = conn.execute(query + ' LIMIT ? OFFSET ?', query_params).fetchall()
    
    # 获取所有班级用于筛选 - 从班级表获取
    all_classes = conn.execute('SELECT DISTINCT class_name FROM classes ORDER BY class_name').fetchall()
    
    conn.close()
    
    # 从Session获取高亮考勤，然后清除Session中的高亮状态
    highlighted_attendance = session.get('highlighted_attendance')
    if highlighted_attendance:
        session.pop('highlighted_attendance', None)
    
    return render_template('attendance.html', records=records, all_classes=all_classes,
                          student_filter=student_filter, class_filter=class_filter, 
                          status_filter=status_filter, major_filter=major_filter,
                          date_filter=date_filter, just_added=just_added, 
                          highlighted_attendance=highlighted_attendance, has_filter=True,
                          page=page, total_pages=total_pages, total=total)

@app.route('/attendance/add', methods=('GET', 'POST'))
def add_attendance():
    """添加考勤"""
    conn = get_db_connection()
    
    # 获取所有班级
    classes = conn.execute('SELECT * FROM classes ORDER BY grade_year DESC, class_name').fetchall()
    
    # 获取所有学生
    all_students = conn.execute('SELECT student_id, name, class_name FROM students ORDER BY class_name, name').fetchall()
    
    students = []
    selected_class = None
    
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        date = request.form['date']
        course_name = request.form.get('course_name', '')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 批量添加考勤
        success_count = 0
        error_count = 0
        
        # 记录成功添加的学生ID列表（用于高亮显示）
        added_student_ids = []
        
        if class_name:
            # 获取该班级的学生
            students_to_add = conn.execute('SELECT student_id FROM students WHERE class_name = ?', (class_name,)).fetchall()
            
            for student in students_to_add:
                student_id = student['student_id']
                status_key = f'status_{student_id}'
                remarks_key = f'remarks_{student_id}'
                status = request.form.get(status_key, '出勤')
                remarks = request.form.get(remarks_key, '')
                if status == '-':
                    continue
                try:
                    conn.execute('''
                        INSERT INTO attendance (student_id, date, status, remarks, course_name, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (student_id, date, status, remarks, course_name, now, now))
                    success_count += 1
                    added_student_ids.append(student_id)
                except Exception:
                    error_count += 1
        
        conn.commit()
        flash(f'成功添加 {success_count} 条考勤记录' + (f'，失败 {error_count} 条' if error_count > 0 else ''), 'success')
        conn.close()
        
        # 清除之前的高亮状态，只高亮最近添加的考勤
        if added_student_ids:
            session['highlighted_attendance'] = ','.join(added_student_ids)
        session.pop('highlighted_class', None)
        session.pop('highlighted_grade', None)
        
        # 跳转到列表主页第一页，显示每个学生的最新记录，并高亮刚添加的学生
        return redirect(url_for('attendance', page=1))
    
    conn.close()
    return render_template('attendance_add.html', students=students, classes=classes, selected_class=selected_class, all_students=all_students)

@app.route('/attendance/edit/<int:id>', methods=('GET', 'POST'))
def edit_attendance(id):
    """编辑考勤"""
    conn = get_db_connection()
    attendance = conn.execute('SELECT * FROM attendance WHERE id = ?', (id,)).fetchone()
    student_id = attendance['student_id']
    edit_date = attendance['date']
    
    if request.method == 'POST':
        date = request.form['date']
        status = request.form['status']
        remarks = request.form['remarks']
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn.execute('''
            UPDATE attendance SET date = ?, status = ?, remarks = ?, updated_at = ? WHERE id = ?
        ''', (date, status, remarks, now, id))
        conn.commit()
        conn.close()
        flash('考勤记录更新成功！', 'success')
        # 回到考勤详情页并高亮显示刚修改的记录
        return redirect(url_for('attendance_detail', student_id=student_id, highlight_id=id))
    
    conn.close()
    return render_template('attendance_edit.html', attendance=attendance, student_id=student_id)

@app.route('/attendance/delete/<int:id>', methods=('POST',))
def delete_attendance(id):
    """删除考勤记录"""
    conn = get_db_connection()
    # 先获取该考勤记录对应的学生ID，以便删除后返回详情页
    attendance = conn.execute('SELECT student_id FROM attendance WHERE id = ?', (id,)).fetchone()
    student_id = attendance['student_id'] if attendance else None
    conn.execute('DELETE FROM attendance WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('考勤记录删除成功！', 'success')
    # 返回考勤详情页
    if student_id:
        return redirect(url_for('attendance_detail', student_id=student_id))
    return redirect(url_for('attendance'))

# 考勤详情页
@app.route('/attendance/detail/<student_id>')
def attendance_detail(student_id):
    """考勤详情 - 显示某学生的考勤统计"""
    from datetime import datetime, timedelta
    
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # 获取日期筛选参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 如果没有筛选日期，默认显示最近30天
    today = datetime.now().strftime('%Y-%m-%d')
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    if not start_date and not end_date:
        start_date = thirty_days_ago
        end_date = today
    
    conn = get_db_connection()
    highlight_id = request.args.get('highlight_id', type=int)
    from_view = request.args.get('from_view', '')
    # 获取学生信息
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
    
    # 构建考勤记录查询（带日期筛选）
    attendance_query = 'SELECT * FROM attendance WHERE student_id = ?'
    attendance_params = [student_id]
    
    if start_date and end_date:
        attendance_query += ' AND date BETWEEN ? AND ?'
        attendance_params.extend([start_date, end_date])
    elif start_date:
        attendance_query += ' AND date >= ?'
        attendance_params.append(start_date)
    elif end_date:
        attendance_query += ' AND date <= ?'
        attendance_params.append(end_date)
    
    # 获取筛选后的考勤总数
    count_query = attendance_query.replace('SELECT *', 'SELECT COUNT(*)')
    total = conn.execute(count_query, attendance_params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 获取考勤记录（带分页）
    offset = (page - 1) * per_page
    attendance_query += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
    attendance_params.extend([per_page, offset])
    all_attendance = conn.execute(attendance_query, attendance_params).fetchall()
    
    # 统计出勤、缺勤、迟到、请假次数（带日期筛选）
    stats_query = 'SELECT status, COUNT(*) as count FROM attendance WHERE student_id = ?'
    stats_params = [student_id]
    
    if start_date and end_date:
        stats_query += ' AND date BETWEEN ? AND ?'
        stats_params.extend([start_date, end_date])
    elif start_date:
        stats_query += ' AND date >= ?'
        stats_params.append(start_date)
    elif end_date:
        stats_query += ' AND date <= ?'
        stats_params.append(end_date)
    
    stats_query += ' GROUP BY status'
    stats = conn.execute(stats_query, stats_params).fetchall()
    
    # 计算总考勤次数
    total_count = sum([row['count'] for row in stats])
    
    # 转换为字典
    attendance_stats = {row['status']: row['count'] for row in stats}
    
    conn.close()
    return render_template('attendance_detail.html', student=student, 
                         attendance=all_attendance, stats=attendance_stats, total_count=total_count,
                         highlight_id=highlight_id,
                         page=page, total_pages=total_pages, total=total,
                         start_date=start_date, end_date=end_date, from_view=from_view)

# 考勤详情页 - 按状态查看
@app.route('/attendance/detail/<student_id>/status/<status>')
def attendance_detail_by_status(student_id, status):
    """考勤详情 - 按状态查看某学生的考勤记录"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # 获取日期筛选参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    conn = get_db_connection()
    
    # 获取学生信息
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
    
    # 构建查询
    attendance_query = 'SELECT * FROM attendance WHERE student_id = ? AND status = ?'
    attendance_params = [student_id, status]
    
    if start_date and end_date:
        attendance_query += ' AND date BETWEEN ? AND ?'
        attendance_params.extend([start_date, end_date])
    elif start_date:
        attendance_query += ' AND date >= ?'
        attendance_params.append(start_date)
    elif end_date:
        attendance_query += ' AND date <= ?'
        attendance_params.append(end_date)
    
    # 获取总数
    count_query = attendance_query.replace('SELECT *', 'SELECT COUNT(*)')
    total = conn.execute(count_query, attendance_params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 分页查询
    offset = (page - 1) * per_page
    attendance_query += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
    attendance_params.extend([per_page, offset])
    all_attendance = conn.execute(attendance_query, attendance_params).fetchall()
    
    conn.close()
    
    status_name = {'出勤': '出勤', '缺勤': '缺勤', '迟到': '迟到', '请假': '请假'}.get(status, status)
    
    return render_template('attendance_detail_by_status.html', student=student, 
                         attendance=all_attendance, status=status, status_name=status_name,
                         page=page, total_pages=total_pages, total=total,
                         start_date=start_date, end_date=end_date)

# ==================== 成绩统计详情页面 ====================

@app.route('/statistics/grade/<range>')
def statistics_grade_detail(range):
    """成绩统计详情 - 按班级和年级统计"""
    grade_start_date = request.args.get('grade_start_date', '')
    grade_end_date = request.args.get('grade_end_date', '')
    major_filter = request.args.get('major', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 将分数段转换为分数范围
    score_conditions = {
        '90-100': 'g.score >= 90',
        '80-89': 'g.score >= 80 AND g.score < 90',
        '70-79': 'g.score >= 70 AND g.score < 80',
        '60-69': 'g.score >= 60 AND g.score < 70',
        '60以下': 'g.score < 60'
    }
    score_condition = score_conditions.get(range, 'g.score >= 0')
    
    # 按班级统计
    class_query = f'''
        SELECT s.class_name, COUNT(*) as count
        FROM grades g
        JOIN students s ON g.student_id = s.student_id
        WHERE {score_condition}
    '''
    class_params = []
    
    if grade_start_date and grade_end_date:
        class_query += ' AND g.exam_date BETWEEN ? AND ?'
        class_params.extend([grade_start_date, grade_end_date])
    elif grade_start_date:
        class_query += ' AND g.exam_date >= ?'
        class_params.append(grade_start_date)
    elif grade_end_date:
        class_query += ' AND g.exam_date <= ?'
        class_params.append(grade_end_date)
    
    if major_filter:
        class_query += ' AND s.major = ?'
        class_params.append(major_filter)
    
    class_query += ' GROUP BY s.class_name ORDER BY count DESC'
    class_stats = conn.execute(class_query, class_params).fetchall()
    
    # 按年级统计
    grade_query = f'''
        SELECT s.grade_year, COUNT(*) as count
        FROM grades g
        JOIN students s ON g.student_id = s.student_id
        WHERE {score_condition}
    '''
    grade_params = []
    
    if grade_start_date and grade_end_date:
        grade_query += ' AND g.exam_date BETWEEN ? AND ?'
        grade_params.extend([grade_start_date, grade_end_date])
    elif grade_start_date:
        grade_query += ' AND g.exam_date >= ?'
        grade_params.append(grade_start_date)
    elif grade_end_date:
        grade_query += ' AND g.exam_date <= ?'
        grade_params.append(grade_end_date)
    
    if major_filter:
        grade_query += ' AND s.major = ?'
        grade_params.append(major_filter)
    
    grade_query += ' GROUP BY s.grade_year ORDER BY count DESC'
    grade_stats = conn.execute(grade_query, grade_params).fetchall()
    
    # 学生成绩列表 - 带分页
    student_query = f'''
        SELECT s.student_id, s.name, s.class_name, s.grade_year, g.score, g.exam_date
        FROM grades g
        JOIN students s ON g.student_id = s.student_id
        WHERE {score_condition}
    '''
    student_params = []
    
    if grade_start_date and grade_end_date:
        student_query += ' AND g.exam_date BETWEEN ? AND ?'
        student_params.extend([grade_start_date, grade_end_date])
    elif grade_start_date:
        student_query += ' AND g.exam_date >= ?'
        student_params.append(grade_start_date)
    elif grade_end_date:
        student_query += ' AND g.exam_date <= ?'
        student_params.append(grade_end_date)
    
    if major_filter:
        student_query += ' AND s.major = ?'
        student_params.append(major_filter)
    
    # 计数查询
    count_query = student_query.replace('SELECT s.student_id, s.name, s.class_name, s.grade_year, g.score, g.exam_date', 'SELECT COUNT(*)')
    total = conn.execute(count_query, tuple(student_params)).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page
    
    # 分页查询
    offset = (page - 1) * per_page
    student_query += ' ORDER BY s.class_name, g.score DESC LIMIT ? OFFSET ?'
    student_params.extend([per_page, offset])
    students = conn.execute(student_query, tuple(student_params)).fetchall()
    
    conn.close()
    
    return render_template('statistics_grade_detail.html', 
                           score_range=range,
                           class_stats=class_stats,
                           grade_stats=grade_stats,
                           students=students,
                           grade_start_date=grade_start_date,
                           grade_end_date=grade_end_date,
                           major_filter=major_filter,
                           page=page, total_pages=total_pages, total=total)

# ==================== 考勤统计详情页面 ====================

@app.route('/statistics/attendance/<status>')
def statistics_attendance_detail(status):
    """考勤统计详情 - 按班级和年级统计"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    major_filter = request.args.get('major', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 按班级统计
    class_query = '''
        SELECT s.class_name, COUNT(*) as count
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.status = ?
    '''
    class_params = [status]
    
    if start_date and end_date:
        class_query += ' AND a.date BETWEEN ? AND ?'
        class_params.extend([start_date, end_date])
    elif start_date:
        class_query += ' AND a.date >= ?'
        class_params.append(start_date)
    elif end_date:
        class_query += ' AND a.date <= ?'
        class_params.append(end_date)
    
    if major_filter:
        class_query += ' AND s.major = ?'
        class_params.append(major_filter)
    
    class_query += ' GROUP BY s.class_name ORDER BY count DESC'
    class_stats = conn.execute(class_query, class_params).fetchall()
    
    # 按年级统计
    grade_query = '''
        SELECT s.grade_year, COUNT(*) as count
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.status = ?
    '''
    grade_params = [status]
    
    if start_date and end_date:
        grade_query += ' AND a.date BETWEEN ? AND ?'
        grade_params.extend([start_date, end_date])
    elif start_date:
        grade_query += ' AND a.date >= ?'
        grade_params.append(start_date)
    elif end_date:
        grade_query += ' AND a.date <= ?'
        grade_params.append(end_date)
    
    if major_filter:
        grade_query += ' AND s.major = ?'
        grade_params.append(major_filter)
    
    grade_query += ' GROUP BY s.grade_year ORDER BY count DESC'
    grade_stats = conn.execute(grade_query, grade_params).fetchall()
    
    # 学生列表 - 带分页
    student_query = '''
        SELECT s.student_id, s.name, s.class_name, s.grade_year, a.date, a.remarks
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.status = ?
    '''
    student_params = [status]
    
    if start_date and end_date:
        student_query += ' AND a.date BETWEEN ? AND ?'
        student_params.extend([start_date, end_date])
    elif start_date:
        student_query += ' AND a.date >= ?'
        student_params.append(start_date)
    elif end_date:
        student_query += ' AND a.date <= ?'
        student_params.append(end_date)
    
    if major_filter:
        student_query += ' AND s.major = ?'
        student_params.append(major_filter)
    
    # 计数查询
    count_query = student_query.replace('SELECT s.student_id, s.name, s.class_name, s.grade_year, a.date, a.remarks', 'SELECT COUNT(*)')
    total = conn.execute(count_query, tuple(student_params)).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page
    
    # 分页查询
    offset = (page - 1) * per_page
    student_query += ' ORDER BY s.class_name, a.date DESC LIMIT ? OFFSET ?'
    student_params.extend([per_page, offset])
    students = conn.execute(student_query, tuple(student_params)).fetchall()
    
    conn.close()
    
    status_name = {'出勤': '出勤', '缺勤': '缺勤', '迟到': '迟到', '请假': '请假'}.get(status, status)
    
    return render_template('statistics_attendance_detail.html', 
                           status=status,
                           status_name=status_name,
                           class_stats=class_stats,
                           grade_stats=grade_stats,
                           students=students,
                           start_date=start_date,
                           end_date=end_date,
                           major_filter=major_filter,
                           page=page, total_pages=total_pages, total=total)

# ==================== 统计页面 ====================

@app.route('/statistics')
def statistics():
    """统计页面"""
    # 获取筛选参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    grade_start_date = request.args.get('grade_start_date', '')
    grade_end_date = request.args.get('grade_end_date', '')
    major_filter = request.args.get('major', '')
    
    conn = get_db_connection()
    
    # 学生统计
    if major_filter:
        total_students = conn.execute('SELECT COUNT(*) FROM students WHERE major = ?', (major_filter,)).fetchone()[0]
        major_stats = conn.execute('''
            SELECT major, COUNT(*) as count 
            FROM students 
            WHERE major = ?
            GROUP BY major 
            ORDER BY count DESC
        ''', (major_filter,)).fetchall()
    else:
        total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        major_stats = conn.execute('''
            SELECT major, COUNT(*) as count 
            FROM students 
            GROUP BY major 
            ORDER BY count DESC
        ''').fetchall()
    
    gender_stats = conn.execute('''
        SELECT gender, COUNT(*) as count 
        FROM students 
        GROUP BY gender
    ''').fetchall()
    
    # 考勤统计 - 根据日期和专业筛选
    attendance_query = '''
        SELECT a.status, COUNT(*) as count 
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
    '''
    attendance_params = []
    conditions = []
    
    if start_date and end_date:
        conditions.append('a.date BETWEEN ? AND ?')
        attendance_params.extend([start_date, end_date])
    elif start_date:
        conditions.append('a.date >= ?')
        attendance_params.append(start_date)
    elif end_date:
        conditions.append('a.date <= ?')
        attendance_params.append(end_date)
    
    if major_filter:
        conditions.append('s.major = ?')
        attendance_params.append(major_filter)
    
    if conditions:
        attendance_query += ' WHERE ' + ' AND '.join(conditions)
    attendance_query += ' GROUP BY a.status'
    
    attendance_stats = conn.execute(attendance_query, attendance_params).fetchall()
    
    # 计算考勤总数
    total_attendance = sum([r['count'] for r in attendance_stats]) if attendance_stats else 0
    
    # 成绩分段统计 - 根据专业和日期筛选
    grade_query = '''
        SELECT 
            CASE 
                WHEN g.score >= 90 THEN '90-100'
                WHEN g.score >= 80 THEN '80-89'
                WHEN g.score >= 70 THEN '70-79'
                WHEN g.score >= 60 THEN '60-69'
                ELSE '60以下'
            END as range,
            COUNT(*) as count
        FROM grades g
        JOIN students s ON g.student_id = s.student_id
    '''
    grade_params = []
    grade_conditions = []
    
    if major_filter:
        grade_conditions.append('s.major = ?')
        grade_params.append(major_filter)
    
    if grade_start_date and grade_end_date:
        grade_conditions.append('g.exam_date BETWEEN ? AND ?')
        grade_params.extend([grade_start_date, grade_end_date])
    elif grade_start_date:
        grade_conditions.append('g.exam_date >= ?')
        grade_params.append(grade_start_date)
    elif grade_end_date:
        grade_conditions.append('g.exam_date <= ?')
        grade_params.append(grade_end_date)
    
    if grade_conditions:
        grade_query += ' WHERE ' + ' AND '.join(grade_conditions)
    
    grade_query += ' AND g.score IS NOT NULL GROUP BY range ORDER BY CASE range WHEN \'90-100\' THEN 1 WHEN \'80-89\' THEN 2 WHEN \'70-79\' THEN 3 WHEN \'60-69\' THEN 4 ELSE 5 END'
    
    grade_stats = conn.execute(grade_query, grade_params).fetchall()
    
    conn.close()
    return render_template('statistics.html', 
                           total_students=total_students,
                           major_stats=major_stats,
                           gender_stats=gender_stats,
                           attendance_stats=attendance_stats,
                           grade_stats=grade_stats,
                           start_date=start_date,
                           end_date=end_date,
                           grade_start_date=grade_start_date,
                           grade_end_date=grade_end_date,
                           total_attendance=total_attendance,
                           major_filter=major_filter)

# ==================== 班级管理 ====================

@app.route('/classes')
def classes():
    """班级列表 - 支持标签页切换（在校班级和已毕业班级）"""
    search_query = request.args.get('search', '')
    major_filter = request.args.get('major', '')
    graduation_status = request.args.get('graduation_status', 'current')  # current: 在校, graduated: 已毕业
    just_added = request.args.get('just_added', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 获取在校班级和已毕业班级的数量统计
    current_classes_count = conn.execute('SELECT COUNT(*) FROM classes WHERE is_graduated = 0').fetchone()[0]
    graduated_classes_count = conn.execute('SELECT COUNT(*) FROM classes WHERE is_graduated = 1').fetchone()[0]
    
    # 构建基础查询条件（用于当前标签页的数据）
    conditions = []
    params = []
    
    if major_filter:
        conditions.append('classes.major = ?')
        params.append(major_filter)
    
    if search_query:
        conditions.append('(classes.class_name LIKE ? OR classes.major LIKE ?)')
        params.extend([f'%{search_query}%', f'%{search_query}%'])
    
    # 根据毕业状态筛选
    if graduation_status == 'graduated':
        conditions.append('classes.is_graduated = 1')
    else:
        conditions.append('classes.is_graduated = 0')
    
    # 构建计数查询
    if conditions:
        count_query = 'SELECT COUNT(*) FROM classes WHERE ' + ' AND '.join(conditions)
        count_params = tuple(params)
    else:
        count_query = 'SELECT COUNT(*) FROM classes'
        count_params = ()
    
    # 获取总记录数
    total = conn.execute(count_query, count_params).fetchone()[0]
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 构建主查询
    base_query = '''
        SELECT classes.*, COUNT(s.id) as student_count
        FROM classes
        LEFT JOIN students s ON classes.class_name = s.class_name
    '''
    
    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)
    
    base_query += ' GROUP BY classes.id ORDER BY classes.updated_at DESC, classes.created_at DESC LIMIT ? OFFSET ?'
    
    # 获取当前页数据
    offset = (page - 1) * per_page
    query_params = tuple(params) + (per_page, offset)
    classes_list = conn.execute(base_query, query_params).fetchall()
    
    # 获取所有班级（用于两个标签页）
    all_classes_query = '''
        SELECT classes.*, COUNT(s.id) as student_count
        FROM classes
        LEFT JOIN students s ON classes.class_name = s.class_name
        GROUP BY classes.id ORDER BY classes.is_graduated, classes.updated_at DESC
    '''
    all_classes = conn.execute(all_classes_query).fetchall()
    
    # 分离在校班级和已毕业班级
    current_classes = [cls for cls in all_classes if cls['is_graduated'] == 0]
    graduated_classes = [cls for cls in all_classes if cls['is_graduated'] == 1]
    
    conn.close()
    
    # 从Session获取高亮班级，然后清除Session中的高亮状态
    highlighted_class = session.get('highlighted_class')
    if highlighted_class:
        session.pop('highlighted_class', None)
    
    return render_template('classes.html', 
                         classes=classes_list, 
                         current_classes=current_classes,
                         graduated_classes=graduated_classes,
                         search_query=search_query, 
                         majors=MAJORS, 
                         major_filter=major_filter,
                         graduation_status=graduation_status,
                         current_classes_count=current_classes_count,
                         graduated_classes_count=graduated_classes_count,
                         just_added=just_added, 
                         highlighted_class=highlighted_class, 
                         page=page, 
                         total_pages=total_pages, 
                         total=total)

@app.route('/classes/add', methods=('GET', 'POST'))
def add_class():
    """添加班级"""
    if request.method == 'POST':
        class_name = request.form['class_name']
        major = request.form['major']
        grade_year = request.form['grade_year']
        
        conn = get_db_connection()
        
        # 1. 首先检查同一专业下是否已存在同名班级（保持现有逻辑）
        existing_same_major = conn.execute(
            'SELECT * FROM classes WHERE class_name = ? AND major = ?',
            (class_name, major)
        ).fetchone()
        
        if existing_same_major:
            conn.close()
            flash(f'该专业下已存在同名班级 "{class_name}"！', 'error')
            return redirect(url_for('add_class'))
        
        # 2. 检查不同专业下是否存在同名班级
        existing_other_major = conn.execute(
            'SELECT * FROM classes WHERE class_name = ? AND major != ?',
            (class_name, major)
        ).fetchone()
        
        original_class_name = class_name  # 保存原始班级名用于提示
        
        if existing_other_major:
            # 不同专业同名字：自动生成新班级名
            # 提取专业名（去掉"系"字）
            major_short = major.replace('系', '')
            new_class_name = f"{major_short}班-{class_name}"
            
            # 检查新班级名是否也存在（避免二次冲突）
            counter = 1
            while conn.execute('SELECT * FROM classes WHERE class_name = ?', (new_class_name,)).fetchone():
                # 如果还存在，添加数字后缀
                new_class_name = f"{major_short}班-{class_name}{counter}"
                counter += 1
            
            class_name = new_class_name
            flash(f'班级名"{original_class_name}"已存在，已自动修改为"{class_name}"', 'info')
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO classes (class_name, major, grade_year, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (class_name, major, grade_year, now, now))
        conn.commit()
        conn.close()
        
        # 只有在班级名没有被重命名的情况下才显示"班级添加成功"消息
        if not existing_other_major:
            flash('班级添加成功！', 'success')
        
        # 清除之前的高亮状态，只高亮最近添加的班级
        session['highlighted_class'] = class_name
        session.pop('highlighted_grade', None)
        session.pop('highlighted_attendance', None)
        
        # 跳转到班级列表第一页，并高亮显示刚添加的班级
        return redirect(url_for('classes', page=1))
    
    return render_template('class_add.html', majors=MAJORS)

@app.route('/classes/edit', methods=('POST',))
def edit_class():
    """编辑班级（弹框提交）"""
    class_id = request.form.get('id')
    class_name = request.form['class_name']
    major = request.form['major']
    grade_year = request.form['grade_year']
    
    if not class_id:
        flash('班级ID不能为空！', 'error')
        return redirect(url_for('classes'))
    
    conn = get_db_connection()
    
    # 1. 首先检查同一专业下是否已存在同名班级（排除自己）
    existing_same_major = conn.execute(
        'SELECT * FROM classes WHERE class_name = ? AND major = ? AND id != ?',
        (class_name, major, class_id)
    ).fetchone()
    
    if existing_same_major:
        conn.close()
        flash(f'该专业下已存在同名班级 "{class_name}"！', 'error')
        return redirect(url_for('classes'))
    
    # 2. 检查不同专业下是否存在同名班级（排除自己）
    existing_other_major = conn.execute(
        'SELECT * FROM classes WHERE class_name = ? AND major != ? AND id != ?',
        (class_name, major, class_id)
    ).fetchone()
    
    original_class_name = class_name  # 保存原始班级名用于提示
    
    if existing_other_major:
        # 不同专业同名字：自动生成新班级名
        # 提取专业名（去掉"系"字）
        major_short = major.replace('系', '')
        new_class_name = f"{major_short}班-{class_name}"
        
        # 检查新班级名是否也存在（避免二次冲突）
        counter = 1
        while conn.execute('SELECT * FROM classes WHERE class_name = ? AND id != ?', (new_class_name, class_id)).fetchone():
            # 如果还存在，添加数字后缀
            new_class_name = f"{major_short}班-{class_name}{counter}"
            counter += 1
        
        class_name = new_class_name
        flash(f'班级名"{original_class_name}"已存在，已自动修改为"{class_name}"', 'info')
    
    # 更新班级信息 - 只更新updated_at，不修改created_at
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('''
        UPDATE classes 
        SET class_name = ?, major = ?, grade_year = ?, updated_at = ?
        WHERE id = ?
    ''', (class_name, major, grade_year, now, class_id))
    conn.commit()
    conn.close()
    
    # 只有在班级名没有被重命名的情况下才显示"班级修改成功"消息
    if not existing_other_major:
        flash('班级修改成功！', 'success')
    
    # 清除之前的高亮状态，只高亮最近修改的班级
    session['highlighted_class'] = class_name
    session.pop('highlighted_grade', None)
    session.pop('highlighted_attendance', None)
    
    # 跳转到班级列表第一页，并高亮显示刚修改的班级
    return redirect(url_for('classes', page=1))

@app.route('/classes/delete', methods=('POST',))
def delete_class():
    """删除班级"""
    id = request.form.get('id')
    if not id:
        flash('班级ID不能为空！', 'error')
        return redirect(url_for('classes'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM classes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('班级删除成功！', 'success')
    return redirect(url_for('classes'))

# ==================== 班级详情管理 ====================

@app.route('/classes/<class_name>')
def class_detail(class_name):
    """班级详情 - 显示班级学生列表（排除未分班的学生）"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 获取班级信息
    cls = conn.execute('SELECT * FROM classes WHERE class_name = ?', (class_name,)).fetchone()
    
    # 获取学生总数（排除未分班的学生）
    total = conn.execute('SELECT COUNT(*) FROM students WHERE class_name = ? AND class_name != ?', 
                         (class_name, '未分班')).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 获取学生（带分页，排除未分班的学生）
    offset = (page - 1) * per_page
    students = conn.execute('''
        SELECT * FROM students 
        WHERE class_name = ? AND class_name != ?
        ORDER BY updated_at DESC, name
        LIMIT ? OFFSET ?
    ''', (class_name, '未分班', per_page, offset)).fetchall()
    
    # 统计学生人数
    student_count = total
    
    conn.close()
    
    # 从Session获取高亮班级学生，然后清除Session中的高亮状态
    highlighted_class_student = session.get('highlighted_class_student')
    if highlighted_class_student:
        session.pop('highlighted_class_student', None)
    
    return render_template('class_detail.html', cls=cls, students=students, student_count=student_count,
                         highlighted_class_student=highlighted_class_student,
                         page=page, total_pages=total_pages, total=total)

@app.route('/classes/<class_name>/add', methods=('GET', 'POST'))
def class_add_student(class_name):
    """班级详情 - 添加学生"""
    conn = get_db_connection()
    
    # 获取班级信息
    cls = conn.execute('SELECT * FROM classes WHERE class_name = ?', (class_name,)).fetchone()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        gender = request.form['gender']
        age = int(request.form['age'])
        major = request.form['major']
        grade_year = request.form.get('grade_year')
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            conn.execute('''
                INSERT INTO students (student_id, name, gender, age, major, class_name, grade_year, phone, email, address, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, name, gender, age, major, class_name, grade_year, phone, email, address, now, now))
            conn.commit()
            flash('学生添加成功！', 'success')
            
            # 获取刚插入的学生ID
            student = conn.execute('SELECT id FROM students WHERE student_id = ?', (student_id,)).fetchone()
            student_id_value = student['id'] if student else None
            
            # 设置高亮标记
            if student_id_value:
                session['highlighted_class_student'] = student_id_value
            
            return redirect(url_for('class_detail', class_name=class_name))
        except sqlite3.IntegrityError:
            flash('学号已存在，请使用不同的学号！', 'error')
        finally:
            conn.close()
    
    conn.close()
    return render_template('class_student_add.html', cls=cls, majors=MAJORS)

@app.route('/classes/<class_name>/edit/<int:student_id>', methods=('GET', 'POST'))
def class_edit_student(class_name, student_id):
    """班级详情 - 编辑学生"""
    conn = get_db_connection()
    
    # 获取班级信息
    cls = conn.execute('SELECT * FROM classes WHERE class_name = ?', (class_name,)).fetchone()
    
    # 获取学生信息
    student = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    
    if request.method == 'POST':
        new_student_id = request.form['student_id']
        name = request.form['name']
        gender = request.form['gender']
        age = int(request.form['age'])
        major = request.form['major']
        grade_year = request.form.get('grade_year')
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            conn.execute('''
                UPDATE students 
                SET student_id=?, name=?, gender=?, age=?, major=?, class_name=?, grade_year=?, phone=?, email=?, address=?, updated_at=?
                WHERE id=?
            ''', (new_student_id, name, gender, age, major, class_name, grade_year, phone, email, address, now, student_id))
            conn.commit()
            flash('学生信息更新成功！', 'success')
            
            # 设置高亮标记
            session['highlighted_class_student'] = student_id
            
            return redirect(url_for('class_detail', class_name=class_name))
        except sqlite3.IntegrityError:
            flash('学号已存在，请使用不同的学号！', 'error')
        finally:
            conn.close()
    
    conn.close()
    return render_template('class_student_edit.html', cls=cls, student=student, majors=MAJORS)

@app.route('/classes/<class_name>/delete/<int:student_id>', methods=('POST',))
def class_delete_student(class_name, student_id):
    """班级详情 - 删除学生（将学生设置为未分班状态）"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    
    # 将学生班级设置为"未分班"，而不是删除记录
    conn.execute('UPDATE students SET class_name = ?, updated_at = ? WHERE id = ?', 
                 ('未分班', now, student_id))
    conn.commit()
    conn.close()
    
    flash('学生已从班级移除，状态变为未分班！', 'success')
    
    # 跳转到编辑学生页面，让学生重新选择专业和班级
    return redirect(url_for('edit_student', id=student_id))

# ==================== 学费管理 ====================

@app.route('/tuition')
def tuition():
    """学费管理页面 - 仅管理员可访问"""
    # 检查是否为管理员
    if session.get('login_type') != 'admin':
        flash('只有管理员才能查看学费管理！', 'error')
        return redirect(url_for('about'))
    
    class_filter = request.args.get('class', '')
    major_filter = request.args.get('major', '')
    status_filter = request.args.get('status', '')
    graduation_status_filter = request.args.get('graduation_status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 获取所有学生及其学费信息
    query = '''
        SELECT * FROM students 
        WHERE enrollment_date IS NOT NULL AND enrollment_date != ''
    '''
    params = []
    
    if class_filter:
        query += ' AND class_name = ?'
        params.append(class_filter)
    if major_filter:
        query += ' AND major = ?'
        params.append(major_filter)
    if graduation_status_filter:
        query += ' AND graduation_status = ?'
        params.append(graduation_status_filter)
    
    query += ' ORDER BY updated_at DESC, major, class_name, name'
    
    students = conn.execute(query, params).fetchall()
    
    # 处理学费状态
    from datetime import datetime, timedelta
    today = datetime.now().date()
    student_data = []
    
    for student in students:
        enrollment_date_str = student['enrollment_date']
        months_paid = student['months_paid'] or 0
        
        # 检查毕业状态
        graduation_status = student['graduation_status'] if 'graduation_status' in student else '在校'
        if graduation_status in ['已毕业', '离校']:
            # 已毕业或离校的学生，显示毕业状态而不是逾期天数
            student_data.append({
                'student': student,
                'enrollment_date': enrollment_date_str,
                'months_paid': months_paid,
                'expiry_date': '-',
                'payment_status': graduation_status,
                'days_until_expiry': None,
                'is_expiring_soon': False,
                'graduation_status': graduation_status
            })
        elif enrollment_date_str:
            try:
                enrollment_date = datetime.strptime(enrollment_date_str, '%Y-%m-%d').date()
                # 到期日期 = 入学日期 + 已缴月数
                expiry_date = enrollment_date + timedelta(days=months_paid * 30)
                
                # 计算状态
                if months_paid == 0:
                    payment_status = '未缴'
                elif months_paid >= 12:
                    payment_status = '已缴'
                else:
                    payment_status = '部分交'
                
                # 计算距离到期的天数
                days_until_expiry = (expiry_date - today).days
                
                # 判断是否需要高亮（到期前一个月内）
                is_expiring_soon = 0 <= days_until_expiry <= 30
                
                student_data.append({
                    'student': student,
                    'enrollment_date': enrollment_date_str,
                    'months_paid': months_paid,
                    'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                    'payment_status': payment_status,
                    'days_until_expiry': days_until_expiry,
                    'is_expiring_soon': is_expiring_soon,
                    'graduation_status': '在校'
                })
            except:
                pass
    
    # 按状态筛选
    if status_filter:
        if status_filter == '未缴':
            student_data = [s for s in student_data if s['payment_status'] == '未缴']
        elif status_filter == '部分交':
            student_data = [s for s in student_data if s['payment_status'] == '部分交']
        elif status_filter == '已缴':
            student_data = [s for s in student_data if s['payment_status'] == '已缴']
        elif status_filter == '即将到期':
            student_data = [s for s in student_data if s['is_expiring_soon']]
        elif status_filter == '已毕业':
            student_data = [s for s in student_data if s['graduation_status'] == '已毕业']
        elif status_filter == '离校':
            student_data = [s for s in student_data if s['graduation_status'] == '离校']
    
    # 分页
    total = len(student_data)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page
    student_data_paged = student_data[offset:offset + per_page]
    
    # 获取所有班级用于筛选
    all_classes = conn.execute('SELECT DISTINCT class_name FROM classes ORDER BY class_name').fetchall()
    
    conn.close()
    
    # 从Session获取高亮学费，然后清除Session中的高亮状态
    highlighted_tuition = session.get('highlighted_tuition')
    if highlighted_tuition:
        session.pop('highlighted_tuition', None)
    
    return render_template('tuition.html', 
                          student_data=student_data_paged,
                          all_classes=all_classes,
                          class_filter=class_filter,
                          major_filter=major_filter,
                          status_filter=status_filter,
                          graduation_status_filter=graduation_status_filter,
                          majors=MAJORS,
                          highlighted_tuition=highlighted_tuition,
                          page=page, total_pages=total_pages, total=total)

@app.route('/tuition/edit/<int:id>', methods=('GET', 'POST'))
def tuition_edit(id):
    """编辑学费信息 - 仅管理员可访问"""
    # 检查是否为管理员
    if session.get('login_type') != 'admin':
        flash('只有管理员才能编辑学费信息！', 'error')
        return redirect(url_for('about'))
    
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        enrollment_date = request.form.get('enrollment_date', '')
        months_paid = int(request.form.get('months_paid', 0))
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn.execute('''
            UPDATE students SET enrollment_date = ?, months_paid = ?, updated_at = ? WHERE id = ?
        ''', (enrollment_date, months_paid, now, id))
        conn.commit()
        conn.close()
        flash('学费信息更新成功！', 'success')
        
        # 设置高亮标记
        session['highlighted_tuition'] = id
        
        return redirect(url_for('tuition'))
    
    conn.close()
    return render_template('tuition_edit.html', student=student)

# ==================== 首页 ====================

@app.route('/')
def home():
    """首页 - 学校介绍页面"""
    try:
        login_type = session.get('login_type')
        username = session.get('username')
        user_id = session.get('user_id')
        # 读取并清除刚编辑的新闻标记
        just_edited = session.get('just_edited_news')
        session.pop('just_edited_news', None)
        # 读取并清除刚编辑的成绩标记
        just_edited_grade = session.get('just_edited_grade')
        session.pop('just_edited_grade', None)
        # 读取并清除刚编辑的考勤标记
        just_edited_attendance = session.get('just_edited_attendance')
        session.pop('just_edited_attendance', None)
    except RuntimeError:
        login_type = None
        username = None
        user_id = None
        just_edited = None
        just_edited_grade = None
        just_edited_attendance = None
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 获取新闻总数
    total = conn.execute('SELECT COUNT(*) FROM news').fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 获取当前页新闻
    offset = (page - 1) * per_page
    news_list = conn.execute('SELECT * FROM news ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    
    conn.close()
    
    return render_template('about.html', current_login_type=login_type, current_username=username, current_user_id=user_id, 
                          just_edited_news=just_edited, news_list=news_list,
                          page=page, total_pages=total_pages, total=total)

# ==================== 学校介绍页面 ====================

@app.route('/about')
def about():
    """学校介绍页面"""
    try:
        login_type = session.get('login_type')
        username = session.get('username')
        user_id = session.get('user_id')
        # 读取并清除刚编辑的新闻标记
        just_edited = session.get('just_edited_news')
        session.pop('just_edited_news', None)
        # 读取并清除刚编辑的成绩标记
        just_edited_grade = session.get('just_edited_grade')
        session.pop('just_edited_grade', None)
        # 读取并清除刚编辑的考勤标记
        just_edited_attendance = session.get('just_edited_attendance')
        session.pop('just_edited_attendance', None)
    except RuntimeError:
        login_type = None
        username = None
        user_id = None
        just_edited = None
        just_edited_grade = None
        just_edited_attendance = None
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    conn = get_db_connection()
    
    # 获取新闻总数
    total = conn.execute('SELECT COUNT(*) FROM news').fetchone()[0]
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 获取当前页新闻
    offset = (page - 1) * per_page
    news_list = conn.execute('SELECT * FROM news ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    
    conn.close()
    
    return render_template('about.html', current_login_type=login_type, current_username=username, current_user_id=user_id, 
                          just_edited_news=just_edited, news_list=news_list,
                          page=page, total_pages=total_pages, total=total)

@app.route('/login', methods=('GET', 'POST'))
def login():
    """登录页面"""
    login_type = request.args.get('type', 'admin')
    
    if request.method == 'POST':
        username = request.form.get('username')
        
        if login_type == 'teacher':
            # 老师登录 - 直接跳转到首页
            session['login_type'] = 'teacher'
            session['username'] = username
            return redirect(url_for('home'))
        else:
            # 管理员登录 - 直接跳转到首页
            session['login_type'] = 'admin'
            session['username'] = username
            return redirect(url_for('home'))
    
    return render_template('login.html', login_type=login_type)

@app.route('/logout')
def logout():
    """退出登录"""
    session.pop('login_type', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('about'))

# ==================== 新闻编辑 ====================

@app.route('/news/edit', methods=('GET', 'POST'))
def news_edit():
    """新闻编辑页面"""
    # 检查是否为管理员
    if session.get('login_type') != 'admin':
        flash('只有管理员才能编辑新闻通知！', 'error')
        return redirect(url_for('about'))
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO news (title, content, time, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, datetime.now().strftime('%m/%d/%Y/%H:%M'), now, now))
        conn.commit()
        conn.close()
        
        flash('新闻添加成功！', 'success')
        return redirect(url_for('about', show_news=1))
    
    return render_template('news_edit.html', title='', content='')

@app.route('/news/detail/<int:index>')
def news_detail(index):
    """新闻详情页面"""
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM news ORDER BY updated_at DESC, id DESC').fetchall()
    conn.close()
    
    # 转换为列表以便按索引访问
    news_list = list(news_list)
    
    if index < 0 or index >= len(news_list):
        flash('新闻不存在！', 'error')
        return redirect(url_for('about'))
    
    # 直接按索引访问（最新的在前）
    news = news_list[index]
    return render_template('news_detail.html', news=news, index=index)

@app.route('/news/edit/<int:index>', methods=('GET', 'POST'))
def news_edit_item(index):
    """编辑单条新闻"""
    # 检查是否为管理员
    if session.get('login_type') != 'admin':
        flash('只有管理员才能编辑新闻！', 'error')
        return redirect(url_for('about'))
    
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM news ORDER BY updated_at DESC, id DESC').fetchall()
    conn.close()
    
    # 转换为列表以便按索引访问
    news_list = list(news_list)
    
    if index < 0 or index >= len(news_list):
        flash('新闻不存在！', 'error')
        return redirect(url_for('about'))
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        
        # 获取原始新闻的时间
        original_news = news_list[index]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE news SET title = ?, content = ?, updated_at = ? WHERE id = ?
        ''', (title, content, now, original_news['id']))
        conn.commit()
        conn.close()
        
        # 标记刚编辑的新闻ID，用于前端显示图标
        session['just_edited_news'] = original_news['id']
        
        flash('新闻修改成功！', 'success')
        return redirect(url_for('about', show_news=1))
    
    news = news_list[index]
    return render_template('news_edit.html', title=news['title'], content=news['content'], edit_index=index)

@app.route('/news/delete/<int:index>', methods=('POST',))
def news_delete(index):
    """删除新闻"""
    # 检查是否为管理员
    if session.get('login_type') != 'admin':
        flash('只有管理员才能删除新闻！', 'error')
        return redirect(url_for('about'))
    
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM news ORDER BY updated_at DESC, id DESC').fetchall()
    conn.close()
    
    # 转换为列表以便按索引访问
    news_list = list(news_list)
    
    if index < 0 or index >= len(news_list):
        flash('新闻不存在！', 'error')
        return redirect(url_for('about'))
    
    # 获取要删除的新闻ID
    news_to_delete = news_list[index]
    
    conn = get_db_connection()
    conn.execute('DELETE FROM news WHERE id = ?', (news_to_delete['id'],))
    conn.commit()
    conn.close()
    
    flash('新闻删除成功！', 'success')
    return redirect(url_for('about', show_news=1))

@app.route('/news')
def news():
    """获取新闻内容（AJAX用）"""
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM news ORDER BY id DESC').fetchall()
    conn.close()
    return {'news_list': [dict(row) for row in news_list]}

# ==================== API 接口 ====================

@app.route('/api/classes/<major>')
def get_classes_by_major(major):
    """获取指定专业的所有班级"""
    conn = get_db_connection()
    classes = conn.execute('SELECT class_name FROM classes WHERE major = ? ORDER BY class_name', (major,)).fetchall()
    conn.close()
    return {'classes': [c['class_name'] for c in classes]}

@app.route('/api/majors')
def get_majors():
    """获取所有专业及其班级"""
    conn = get_db_connection()
    classes = conn.execute('SELECT major, class_name FROM classes ORDER BY major, class_name').fetchall()
    conn.close()
    
    # 按专业分组
    majors_dict = {}
    for c in classes:
        if c['major'] not in majors_dict:
            majors_dict[c['major']] = []
        majors_dict[c['major']].append(c['class_name'])
    
    return {'majors': majors_dict}

# ==================== 毕业状态管理 ====================

@app.route('/classes/<class_name>/graduate', methods=('POST',))
def graduate_class(class_name):
    """批量设置班级为毕业状态"""
    conn = get_db_connection()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 1. 将班级的 is_graduated 设置为 1
        conn.execute('UPDATE classes SET is_graduated = 1, updated_at = ? WHERE class_name = ?', (now, class_name))
        
        # 2. 将该班级所有学生的 graduation_status 设置为 "已毕业"
        conn.execute('UPDATE students SET graduation_status = "已毕业", updated_at = ? WHERE class_name = ?', (now, class_name))
        
        conn.commit()
        conn.close()
        
        flash(f'班级 "{class_name}" 已成功设置为毕业状态！', 'success')
        return redirect(url_for('classes', graduation_status='graduated'))
    except Exception as e:
        conn.close()
        flash(f'设置毕业状态失败: {str(e)}', 'error')
        return redirect(url_for('classes'))

if __name__ == '__main__':
    app.run(debug=True, port=1122)
