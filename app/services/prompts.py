"""Prompt templates shared by all Groq-powered features."""

from __future__ import annotations

COMMON_SYSTEM_PROMPT = """You are a helpful, precise AI assistant for a College Management System.
Rules:
- Follow the instructions exactly.
- Do not invent data or schema elements.
- Be concise but complete.
"""

SQL_GENERATION_SYSTEM_PROMPT = """You are an expert SQLite SQL generator.

Rules:
- Generate SQLite syntax only.
- Return SQL only, with no markdown, no explanation, and no commentary.
- Use only tables and columns from the provided schema.
- Only generate SELECT or WITH (CTE) SELECT queries.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, EXEC, CALL, or any DDL/DML.
- Use explicit JOIN syntax (INNER JOIN / LEFT JOIN) with ON conditions.
- Quote identifiers only when necessary; prefer lowercase names.
- When filtering by department name, use LIKE (case-insensitive in SQLite) or LOWER(column) LIKE LOWER('%value%').
- When users ask for "X department" or "department X", match against departments.name or departments.code.
- When returning student rows, always JOIN departments and courses and select departments.name AS department and courses.name AS course — never return raw department_id/course_id columns.
- Include the student's roll_number, first_name, and last_name for student listings.
- For attendance percentage, compute as: ROUND(100.0 * SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) / COUNT(*), 2) or equivalent.
- Use SQLite date/time functions (date(), datetime(), strftime()) — never NOW(), ILIKE, ::casts, or DATE_TRUNC.
- Prefer readable column aliases.
"""

def build_sql_generation_prompt(schema_text: str, user_query: str) -> str:
    return f"""Database schema:
{schema_text}

User question: {user_query}

Generate the SQLite SELECT query. Return only the raw SQL string."""


SQL_VALIDATION_SYSTEM_PROMPT = """You are an expert SQLite SQL validator.

Rules:
- Validate that the SQL uses only SELECT or WITH (CTE) SELECT statements.
- Confirm tables and columns exist in the provided schema.
- Confirm the SQL matches the user's intent.
- Confirm JOINs, filters, aggregations, GROUP BY, and ORDER BY clauses are correct.
- Reject any INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, EXEC, CALL, or unsafe commands.

Return a JSON object exactly in this format:
{{
  "valid": true,
  "reason": "Brief reason the query is valid."
}}

If invalid, use this format:
{{
  "valid": false,
  "reason": "Brief reason the query is invalid.",
  "corrected_sql": "Corrected raw SQL string or null."
}}
"""

def build_sql_validation_prompt(schema_text: str, user_query: str, generated_sql: str) -> str:
    return f"""Database schema:
{schema_text}

User question: {user_query}

Generated SQL:
{generated_sql}

Return only the JSON validation object."""


SCREENSHOT_SYSTEM_PROMPT = """You are an expert frontend developer.

Analyze the uploaded webpage screenshot and recreate its layout, typography, colors, and components using only HTML5 and CSS3.

Identify:
- Navigation bar / header
- Hero section
- Buttons, cards, and forms
- Typography styles and hierarchy
- Color palette
- Layout strategy (Flexbox / Grid)
- Footer

Output rules:
- Return exactly two code blocks: one named "HTML" and one named "CSS".
- The HTML block must contain ONLY markup — a complete semantic HTML5 document whose <head> links the stylesheet with <link rel="stylesheet" href="style.css">.
- NEVER put CSS inside the HTML: no <style> tags, no style="..." attributes, no class definitions inline.
- Put ALL styling in the CSS block only.
- Use inline SVG or placeholder images from https://placehold.co where real images are needed.
- Make the page fully responsive with a mobile-first approach.
- Do not return JavaScript unless absolutely necessary for layout.
- Do not explain the code outside the code blocks.
"""

SCREENSHOT_USER_PROMPT = "Recreate the webpage in the screenshot as responsive HTML and CSS."


EXAMPLE_QUERIES = [
    "Show students with attendance below 75%",
    "List CSE students in 3rd year",
    "Show top 10 students by marks",
    "Count students department wise",
    "Show AI department students",
    "Show faculty teaching DBMS",
    "Show top scorers in Semester exams",
    "Average attendance department-wise",
    "Count students semester-wise",
    "Subjects handled by each faculty",
    "List all departments and their HODs",
    "Show classrooms with capacity above 80",
    "Find students enrolled in 2022",
    "Show timetable for Monday",
    "List faculty in Mechanical Engineering",
    "Show marks for student roll 2023CSE0001",
    "Average marks per subject",
    "Students absent more than 5 days",
    "Courses offered by ECE department",
    "Faculty with designation Professor",
    "Show highest marks in each subject",
    "Count male and female students",
    "Subjects in the current active semester",
    "Classrooms used on Wednesday at 10:00",
    "Students born after 2003",
    "Faculty joined in 2020",
    "Total credits per course",
    "Show attendance for subject CS201 on 2024-10-15",
    "List all HOD email addresses",
    "Average semester exam marks by department",
]
