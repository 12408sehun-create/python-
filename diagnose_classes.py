import sqlite3
import sys

def diagnose_classes():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    
    print("=== 班级管理诊断 ===")
    
    # 1. 检查表结构
    print("\n1. classes表结构:")
    cursor.execute('PRAGMA table_info(classes)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} ({col[2]}) - PK: {col[5]}")
    
    # 2. 检查是否有缺失的字段
    expected_columns = ['id', 'class_name', 'major', 'grade_year', 'created_at', 'updated_at']
    actual_columns = [col[1] for col in columns]
    missing = [col for col in expected_columns if col not in actual_columns]
    print(f"\n2. 缺失的字段: {missing}")
    
    # 3. 测试查询
    print("\n3. 测试app.py中的关键查询:")
    try:
        # 测试classes()函数中的查询
        query1 = """
            SELECT classes.*, COUNT(s.id) as student_count
            FROM classes
            LEFT JOIN students s ON classes.class_name = s.class_name
            GROUP BY classes.id
            ORDER BY classes.grade_year DESC, classes.major, classes.class_name
            LIMIT 5
        """
        print("   测试classes()查询...")
        cursor.execute(query1)
        results = cursor.fetchall()
        print(f"   查询成功，返回{len(results)}条记录")
    except Exception as e:
        print(f"   查询失败: {e}")
    
    # 4. 检查数据
    print("\n4. 检查班级数据:")
    cursor.execute('SELECT COUNT(*) FROM classes')
    count = cursor.fetchone()[0]
    print(f"   总班级数: {count}")
    
    # 5. 检查孤立的学生班级
    cursor.execute('SELECT DISTINCT class_name FROM students WHERE class_name NOT IN (SELECT class_name FROM classes)')
    orphaned = cursor.fetchall()
    print(f"   孤立的班级名（有学生但没有对应班级）: {len(orphaned)}个")
    for cls in orphaned[:10]:  # 只显示前10个
        print(f"     - {cls[0]}")
    if len(orphaned) > 10:
        print(f"     ... 还有{len(orphaned)-10}个")
    
    # 6. 尝试修复（仅诊断）
    print("\n5. 修复建议:")
    if 'created_at' in missing:
        print("   - 需要添加created_at字段: ALTER TABLE classes ADD COLUMN created_at TEXT")
    if 'updated_at' in missing:
        print("   - 需要添加updated_at字段: ALTER TABLE classes ADD COLUMN updated_at TEXT")
    
    conn.close()
    
    print("\n=== 诊断完成 ===")

if __name__ == '__main__':
    diagnose_classes()