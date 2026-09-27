"""Generate and/or seed realistic dummy data for the College Management System.

Usage:
    python -m app.database.seed --sql-only     # writes app/database/dummy_data.sql
    python -m app.database.seed --execute      # seeds the local SQLite DB
    python -m app.database.seed                # does both
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from app import config

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Ayaan", "Krishna", "Ishaan", "Shaurya",
    "Ananya", "Diya", "Saanvi", "Aadhya", "Navya", "Ira", "Myra", "Pari", "Sara", "Tara",
    "Rahul", "Rohit", "Karan", "Arnav", "Yash", "Kabir", "Veer", "Aryan", "Dev", "Om",
    "Priya", "Kavya", "Meera", "Nisha", "Riya", "Simran", "Tanvi", "Zara", "Ishita", "Neha",
    "Mohammed", "Ayaan", "Faizan", "Imran", "Zaid", "Rehan", "Arif", "Farhan", "Sameer", "Tariq",
    "Fatima", "Zainab", "Maryam", "Ayesha", "Khushi", "Lakshmi", "Radha", "Sunita", "Deepa", "Gauri",
]

LAST_NAMES = [
    "Sharma", "Kumar", "Singh", "Patel", "Gupta", "Reddy", "Nair", "Rao", "Mehta", "Joshi",
    "Shah", "Agarwal", "Verma", "Yadav", "Iyer", "Desai", "Bose", "Banerjee", "Chakraborty",
    "Pandey", "Mishra", "Tiwari", "Jain", "Malhotra", "Khanna", "Chopra", "Bhat", "Menon",
    "Ranganathan", "Srinivasan", "Subramanian", "Venkataraman", "Krishnamurthy", "Mukherjee",
]

DEPARTMENTS = [
    ("Computer Science and Engineering", "CSE"),
    ("Artificial Intelligence and Machine Learning", "AIML"),
    ("Electronics and Communication Engineering", "ECE"),
    ("Electrical and Electronics Engineering", "EEE"),
    ("Mechanical Engineering", "MECH"),
    ("Civil Engineering", "CIVIL"),
    ("Information Technology", "IT"),
    ("Data Science", "DS"),
    ("Cyber Security", "CYBER"),
    ("Bio Technology", "BIO"),
]

COURSES = [
    ("B.Tech Computer Science and Engineering", "BTECH_CSE", 4),
    ("B.Tech Artificial Intelligence", "BTECH_AIML", 4),
    ("B.Tech Electronics and Communication", "BTECH_ECE", 4),
    ("B.Tech Electrical and Electronics", "BTECH_EEE", 4),
    ("B.Tech Mechanical Engineering", "BTECH_MECH", 4),
    ("B.Tech Civil Engineering", "BTECH_CIVIL", 4),
    ("B.Tech Information Technology", "BTECH_IT", 4),
    ("B.Tech Data Science", "BTECH_DS", 4),
]

DESIGNATIONS = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer", "HOD"]

BUILDINGS = ["Main Block", "Science Block", "Engineering Block", "Library Block", "Research Block"]
ROOM_TYPES = ["Lecture Hall", "Lab", "Seminar Room", "Tutorial Room"]

SUBJECT_TEMPLATES = {
    "CSE": [
        ("Data Structures and Algorithms", "CS201", 4),
        ("Database Management Systems", "CS202", 4),
        ("Operating Systems", "CS203", 3),
        ("Computer Networks", "CS204", 3),
        ("Software Engineering", "CS205", 3),
        ("Theory of Computation", "CS301", 3),
        ("Compiler Design", "CS302", 3),
        ("Web Technologies", "CS303", 3),
    ],
    "AIML": [
        ("Introduction to AI", "AI201", 4),
        ("Machine Learning", "AI202", 4),
        ("Deep Learning", "AI301", 3),
        ("Natural Language Processing", "AI302", 3),
        ("Computer Vision", "AI303", 3),
    ],
    "ECE": [
        ("Digital Signal Processing", "EC201", 4),
        ("Analog Circuits", "EC202", 4),
        ("Communication Systems", "EC203", 3),
        ("VLSI Design", "EC301", 3),
    ],
    "EEE": [
        ("Electrical Machines", "EE201", 4),
        ("Power Systems", "EE202", 4),
        ("Control Systems", "EE203", 3),
    ],
    "MECH": [
        ("Thermodynamics", "ME201", 4),
        ("Fluid Mechanics", "ME202", 3),
        ("Manufacturing Processes", "ME203", 3),
    ],
    "CIVIL": [
        ("Structural Analysis", "CE201", 4),
        ("Geotechnical Engineering", "CE202", 3),
        ("Transportation Engineering", "CE203", 3),
    ],
    "IT": [
        ("Cloud Computing", "IT201", 3),
        ("Information Security", "IT202", 3),
        ("Internet of Things", "IT301", 3),
    ],
    "DS": [
        ("Statistics for Data Science", "DS201", 4),
        ("Big Data Analytics", "DS202", 3),
        ("Data Visualization", "DS203", 3),
    ],
}


def escape_sql(value: object) -> str:
    """Escape a Python value into a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (date, datetime)):
        return f"'{value.isoformat()}'"
    text = str(value).replace("'", "''")
    return f"'{text}'"


def insert_statement(table: str, columns: list[str], rows: list[tuple]) -> str:
    """Build a multi-row INSERT statement."""
    if not rows:
        return ""
    col_sql = ", ".join(f'"{c}"' for c in columns)
    values = []
    for row in rows:
        values.append("(" + ", ".join(escape_sql(v) for v in row) + ")")
    return f"INSERT INTO {table} ({col_sql}) VALUES\n" + ",\n".join(values) + ";\n"


def generate_data(seed: int = 42) -> dict[str, list[tuple]]:
    random.seed(seed)

    academic_years = ["2023-24", "2024-25", "2025-26"]
    semesters = []
    semester_id = 0
    for year in academic_years:
        for term in range(1, 3):
            semester_id += 1
            start = date(2024 if term == 1 else 2025, 7 if term == 1 else 1, 15)
            end = start + timedelta(days=150)
            active = term == 1 and year == "2024-25"
            semesters.append((semester_id, year, term, start, end, active))

    departments = []
    for idx, (name, code) in enumerate(DEPARTMENTS, start=1):
        est = 1990 + idx * 2
        departments.append((idx, name, code, est, None, f"Block {idx}"))

    courses = []
    for idx, (name, code, years) in enumerate(COURSES, start=1):
        dept_id = idx  # each course mapped to a distinct department
        credits = years * 20
        courses.append((idx, dept_id, name, code, years, credits))

    faculty = []
    faculty_id = 0
    for dept_id, _ in enumerate(DEPARTMENTS, start=1):
        count = 6
        for i in range(count):
            faculty_id += 1
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email = f"{first.lower()}.{last.lower()}.{faculty_id}@college.edu"
            phone = f"9{random.randint(100000000, 999999999)}"
            designation = random.choice(DESIGNATIONS[:-1]) if i > 0 else "HOD"
            joining = date(random.randint(2010, 2023), random.randint(1, 12), random.randint(1, 28))
            faculty.append((faculty_id, dept_id, first, last, email, phone, designation, joining))

    # Assign HOD references.
    dept_with_hod = []
    for dept in departments:
        dept_id = dept[0]
        hod = next((f[0] for f in faculty if f[1] == dept_id and f[6] == "HOD"), None)
        dept_with_hod.append((dept_id, dept[1], dept[2], dept[3], hod, dept[5]))
    departments = dept_with_hod

    students = []
    for i in range(1, 501):
        dept_id = random.randint(1, len(DEPARTMENTS))
        course_id = min(dept_id, len(COURSES))
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        roll = f"{random.randint(2020, 2024)}{courses[course_id - 1][3]}{i:04d}"
        email = f"{first.lower()}.{last.lower()}.{i}@student.edu"
        phone = f"8{random.randint(100000000, 999999999)}"
        year = 2020 + (i % 5)
        sem_id = random.randint(1, len(semesters))
        gender = random.choice(["Male", "Female", "Other"])
        dob = date(random.randint(2000, 2005), random.randint(1, 12), random.randint(1, 28))
        admission = date(year, random.randint(6, 9), random.randint(1, 28))
        students.append((i, dept_id, course_id, roll, first, last, email, phone, year, sem_id, gender, dob, admission))

    subjects = []
    subject_id = 0
    for sem in semesters:
        sem_id = sem[0]
        for course_id, course in enumerate(courses, start=1):
            dept_id = course[1]
            course_code = course[3]
            templates = SUBJECT_TEMPLATES.get(course_code.split("_")[1], SUBJECT_TEMPLATES["CSE"])
            chosen = random.sample(templates, min(4, len(templates)))
            for name, code_base, credits in chosen:
                subject_id += 1
                code = f"{code_base}_{sem_id}"
                subjects.append((subject_id, course_id, name, code, credits, sem_id))

    attendance = []
    subject_by_id = {s[0]: s for s in subjects}
    for student in students:
        student_id = student[0]
        sem_id = student[9]
        relevant_subjects = [s for s in subjects if s[5] == sem_id]
        if not relevant_subjects:
            relevant_subjects = subjects
        days = random.randint(15, 30)
        for _ in range(days):
            subject = random.choice(relevant_subjects)
            attendance_date = date(2024, random.randint(8, 11), random.randint(1, 28))
            status = random.choices(["present", "absent", "late"], weights=[80, 15, 5])[0]
            attendance.append((
                len(attendance) + 1,
                student_id,
                subject[0],
                sem_id,
                attendance_date,
                status,
                1,
            ))

    marks = []
    for student in students:
        student_id = student[0]
        sem_id = student[9]
        relevant_subjects = [s for s in subjects if s[5] == sem_id]
        if not relevant_subjects:
            relevant_subjects = subjects
        exam_types = ["Internal 1", "Internal 2", "Assignment", "Semester"]
        for subject in relevant_subjects:
            for exam_type in random.sample(exam_types, k=random.randint(2, 4)):
                max_marks = 100 if exam_type == "Semester" else random.choice([20, 25, 50])
                marks_obtained = round(random.uniform(max_marks * 0.35, max_marks), 2)
                exam_date = date(2024, random.randint(8, 11), random.randint(1, 28))
                marks.append((len(marks) + 1, student_id, subject[0], sem_id, exam_type, marks_obtained, max_marks, exam_date))

    classrooms = []
    room_id = 0
    for building in BUILDINGS:
        for floor in range(1, 5):
            for room in range(1, 6):
                room_id += 1
                room_number = f"{floor}0{room}"
                capacity = random.choice([40, 60, 80, 120])
                room_type = random.choice(ROOM_TYPES)
                classrooms.append((room_id, building, room_number, capacity, room_type))

    timetable = []
    slot_templates = [
        ("09:00:00", "10:30:00"),
        ("10:45:00", "12:15:00"),
        ("13:15:00", "14:45:00"),
        ("15:00:00", "16:30:00"),
    ]
    used = set()
    for sem in semesters:
        sem_subjects = [s for s in subjects if s[5] == sem[0]]
        if not sem_subjects:
            sem_subjects = subjects
        for subject in sem_subjects:
            faculty_list = [f for f in faculty if f[1] == courses[subject[1] - 1][1]]
            if not faculty_list:
                faculty_list = faculty
            instructor = random.choice(faculty_list)
            for _ in range(2):
                day = random.randint(1, 6)
                slot = random.choice(slot_templates)
                classroom = random.choice(classrooms)
                key = (sem[0], day, slot[0], classroom[0])
                if key in used:
                    continue
                used.add(key)
                timetable.append((len(timetable) + 1, subject[0], instructor[0], classroom[0], sem[0], day, slot[0], slot[1]))

    return {
        "departments": departments,
        "semesters": semesters,
        "courses": courses,
        "faculty": faculty,
        "students": students,
        "subjects": subjects,
        "attendance": attendance,
        "marks": marks,
        "classrooms": classrooms,
        "timetable": timetable,
    }


def build_sql(data: dict[str, list[tuple]]) -> str:
    lines = [
        "-- Generated dummy data for College Management System\n",
        "DELETE FROM timetable;\nDELETE FROM marks;\nDELETE FROM attendance;\nDELETE FROM subjects;\nDELETE FROM students;\nDELETE FROM faculty;\nDELETE FROM courses;\nDELETE FROM semesters;\nDELETE FROM classrooms;\nDELETE FROM departments;\n",
        "DELETE FROM sqlite_sequence WHERE name IN ('timetable','marks','attendance','subjects','students','faculty','courses','semesters','classrooms','departments');\n",
    ]

    lines.append(insert_statement("departments", ["id", "name", "code", "established_year", "hod_id", "location"], data["departments"]))
    lines.append(insert_statement("semesters", ["id", "academic_year", "term", "start_date", "end_date", "is_active"], data["semesters"]))
    lines.append(insert_statement("courses", ["id", "department_id", "name", "code", "duration_years", "total_credits"], data["courses"]))
    lines.append(insert_statement("faculty", ["id", "department_id", "first_name", "last_name", "email", "phone", "designation", "joining_date"], data["faculty"]))
    lines.append(insert_statement("students", ["id", "department_id", "course_id", "roll_number", "first_name", "last_name", "email", "phone", "enrollment_year", "current_semester_id", "gender", "date_of_birth", "admission_date"], data["students"]))
    lines.append(insert_statement("subjects", ["id", "course_id", "name", "code", "credits", "semester_id"], data["subjects"]))
    lines.append(insert_statement("attendance", ["id", "student_id", "subject_id", "semester_id", "attendance_date", "status", "hours"], data["attendance"]))
    lines.append(insert_statement("marks", ["id", "student_id", "subject_id", "semester_id", "exam_type", "marks_obtained", "max_marks", "exam_date"], data["marks"]))
    lines.append(insert_statement("classrooms", ["id", "building", "room_number", "capacity", "room_type"], data["classrooms"]))
    lines.append(insert_statement("timetable", ["id", "subject_id", "faculty_id", "classroom_id", "semester_id", "day_of_week", "start_time", "end_time"], data["timetable"]))

    # Fix HOD foreign keys after faculty rows are inserted.
    lines.append("\n-- Link department heads\n")
    for dept in data["departments"]:
        if dept[4]:
            lines.append(f"UPDATE departments SET hod_id = {dept[4]} WHERE id = {dept[0]};\n")

    lines.append(f"\n-- Summary counts\n")
    for table in ["departments", "semesters", "courses", "faculty", "students", "subjects", "attendance", "marks", "classrooms", "timetable"]:
        lines.append(f"-- {table}: {len(data[table])} rows\n")

    return "".join(lines)


def seed_database(sql: str) -> None:
    db_path = Path(config.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.executescript(sql)
        conn.commit()
        print(f"Database seeded successfully at {db_path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed college management database")
    parser.add_argument("--sql-only", action="store_true", help="Only generate dummy_data.sql")
    parser.add_argument("--execute", action="store_true", help="Execute generated SQL against the SQLite DB")
    args = parser.parse_args()

    data = generate_data()
    sql = build_sql(data)

    sql_path = Path(__file__).with_name("dummy_data.sql")
    sql_path.write_text(sql, encoding="utf-8")
    print(f"Wrote {sql_path}")

    if not args.sql_only or args.execute:
        seed_database(sql)


if __name__ == "__main__":
    main()
