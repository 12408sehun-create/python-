import sqlite3

conn = sqlite3.connect('college.db')
cursor = conn.cursor()

print("当前数据库中的班级数据：")
cursor.execute('SELECT id, class_name, major, grade_year FROM classes ORDER BY major, class_name')
rows = cursor.fetchall()

if rows:
    for row in rows:
        print(f'ID: {row[0]}, 班级名: {row[1]}, 专业: {row[2]}, 年级: {row[3]}')
else:
    print('数据库中没有班级数据')

conn.close()