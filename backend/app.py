from flask import Flask, jsonify, request
import mysql.connector
from werkzeug.utils import secure_filename
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__)
CORS(app)

app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}  # Allowed file types

# MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="password",
        database="assignmentmanager"
    )
    return connection

# Register Route (Student)
# Register Route (Student)
@app.route('/api/student-register', methods=['POST'])
def student_register():
    data = request.json
    srn = data.get('id')
    name = data.get('name')
    email = data.get('email')
    branch = data.get('branch')
    password = data.get('password')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Insert student details into Student table
        cursor.execute(
            "INSERT INTO Student (SRN, Name, Email, Branch, Password) VALUES (%s, %s, %s, %s, %s)",
            (srn, name, email, branch, hashed_password)
        )
        connection.commit()

        cursor.execute(
            "SELECT DepartmentID FROM Department WHERE DepartmentName = %s", 
            (branch,)
        )
        department = cursor.fetchone()

        # If the department is not found, return an error
        if not department:
            return jsonify({'success': False, 'message': 'Invalid branch name'}), 400

        department_id = department[0]

        # Now, get all the courses for this department (branch)
        cursor.execute(
            "SELECT CourseID FROM Course WHERE DepartmentID = %s", 
            (department_id,)
        )
        courses = cursor.fetchall()

        # Now add the student to the StudentCourse table for each course
        for course in courses:
            course_id = course[0]  # Extract CourseID from the tuple
            cursor.execute(
                "INSERT INTO StudentCourse (SRN, CourseID) VALUES (%s, %s)",
                (srn, course_id)
            )
        connection.commit()


        return jsonify({'success': True, 'message': 'Student registered successfully'}), 200
    except mysql.connector.Error as err:
        print("Error registering student:", err)
        return jsonify({'success': False, 'message': 'Registration failed'}), 500
    finally:
        cursor.close()
        connection.close()


# Register Route (Teacher)
@app.route('/api/teacher-register', methods=['POST'])
def teacher_register():
    data = request.json
    trn = data.get('id')
    name = data.get('name')
    email = data.get('email')
    department_name = data.get('branch')  # Teacher's department
    password = data.get('password')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Insert teacher details into Teacher table
        cursor.execute(
            "INSERT INTO Teacher (TRN, Name, Email, Password) VALUES (%s, %s, %s, %s)",
            (trn, name, email, hashed_password)
        )
        connection.commit()

        # Fetch the DepartmentID for the provided department_name
        cursor.execute(
            "SELECT DepartmentID FROM Department WHERE DepartmentName = %s", 
            (department_name,)
        )
        department = cursor.fetchone()

        # If the department is not found, return an error
        if not department:
            return jsonify({'success': False, 'message': 'Invalid department name'}), 400

        department_id = department[0]

        # Now, get all the courses for this department (department_name)
        cursor.execute(
            "SELECT CourseID FROM Course WHERE DepartmentID = %s", 
            (department_id,)
        )
        courses = cursor.fetchall()

        # Now add the teacher to the TeacherCourse table for each course
        for course in courses:
            course_id = course[0]  # Extract CourseID from the tuple
            cursor.execute(
                "INSERT INTO TeacherCourse (TRN, CourseID) VALUES (%s, %s)",
                (trn, course_id)
            )
        connection.commit()

        return jsonify({'success': True, 'message': 'Teacher registered successfully'}), 200
    except mysql.connector.Error as err:
        print("Error registering teacher:", err)
        return jsonify({'success': False, 'message': 'Registration failed'}), 500
    finally:
        cursor.close()
        connection.close()



# Login Route (Student/Teacher)
@app.route('/api/student-login', methods=['POST'])
def student_login():
    data = request.json
    srn = data.get('id')
    password = data.get('password')
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student WHERE SRN = %s AND Password = %s", (srn, hashed_password))
    student = cursor.fetchone()
    cursor.close()
    connection.close()

    if student:
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid ID or Password'}), 400

# Login Route (Teacher)
@app.route('/api/teacher-login', methods=['POST'])
def teacher_login():
    data = request.json
    trn = data.get('id')
    password = data.get('password')
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teacher WHERE TRN = %s and Password = %s", (trn,hashed_password))
    teacher = cursor.fetchone()
    cursor.close()
    connection.close()

    if teacher:
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid ID or Password'}), 400


# Submit Marks and Comments (Teachers)
@app.route('/api/submit-marks-comments', methods=['POST'])
def submit_marks_comments():
    data = request.json
    student_id = data.get('studentId')
    assignment_id = data.get('assignmentId')
    marks_awarded = data.get('marksAwarded')
    comments = data.get('comments')

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE Marks SET MarksAwarded = %s, Comments = %s WHERE SRN = %s AND AssignmentID = %s",
            (marks_awarded, comments, student_id, assignment_id)
        )
        connection.commit()
        return jsonify({'success': True, 'message': 'Marks and comments submitted successfully'}), 200
    except mysql.connector.Error as err:
        print("Error submitting marks/comments:", err)
        return jsonify({'success': False, 'message': 'Error submitting marks/comments'}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/courses', methods=['GET'])
def get_courses():
    # Fetch the department names from the Department table
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Query to fetch all department names
    cursor.execute("""
        SELECT DepartmentName FROM Department
    """)
    
    departments = cursor.fetchall()
    cursor.close()
    connection.close()

    if departments:
        return jsonify({"success" : True , "departments": [department['DepartmentName'] for department in departments]}), 200
    else:
        return jsonify({"success" : False , "error": "No departments found"}), 404
    
# API to get courses for a student from studentcourse table (grouped by StudentID)
@app.route('/api/student-courses', methods=['GET'])
def get_student_courses():
    student_id = request.args.get('ID')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Call the stored procedure to fetch courses for a student
        cursor.callproc('GetStudentCourses', [student_id])

        # Collect the result sets from the stored procedure
        courses = []
        for result in cursor.stored_results():
            courses.extend(result.fetchall())

        # Return the grouped list of courses as a JSON response
        return jsonify({'success': True, 'courses': courses})
    
    except Exception as e:
        print(f"Error fetching student courses: {e}")
        return jsonify({'success': False, 'message': 'Error fetching courses'}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/teacher-courses', methods=['GET'])
def get_teacher_courses():
    teacher_id = request.args.get('ID')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Call the stored procedure to fetch courses for a teacher
        cursor.callproc('GetTeacherCourses', [teacher_id])

        # Collect the result sets from the stored procedure
        courses = []
        for result in cursor.stored_results():
            courses.extend(result.fetchall())

        # Return the grouped list of courses as a JSON response
        return jsonify({'success': True, 'courses': courses})
    
    except Exception as e:
        print(f"Error fetching teacher courses: {e}")
        return jsonify({'success': False, 'message': 'Error fetching courses'}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student-assignments', methods=['GET'])
def student_assignments():
    student_id = request.args.get('ID')
    course_id = request.args.get('courseId')  # New parameter for course filter

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if course_id:
            # Fetch student assignments for a specific course via procedure
            cursor.callproc('GetStudentAssignmentsByCourse', [student_id, course_id])
        else:
            # Fetch all student assignments as per the original functionality
            cursor.callproc('GetStudentAssignments', [student_id])

        assignments = []
        for result in cursor.stored_results():
            assignments.extend(result.fetchall())

        return jsonify({'success': True, 'assignments': assignments})
    
    except mysql.connector.Error as err:
        print("Error fetching student assignments:", err)
        return jsonify({'success': False, 'message': 'Error fetching assignments'}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/api/teacher-assignments', methods=['GET'])
def teacher_assignments():
    teacher_id = request.args.get('ID')
    course_id = request.args.get('courseId')  # New parameter for course filter

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if course_id:
            # Fetch teacher assignments for a specific course via procedure
            cursor.callproc('GetTeacherAssignmentsByCourse', [teacher_id, course_id])
        else:
            # Fetch all teacher assignments as per the original functionality
            cursor.callproc('GetTeacherAssignments', [teacher_id])

        assignments = []
        for result in cursor.stored_results():
            assignments.extend(result.fetchall())

        return jsonify({'success': True, 'assignments': assignments})

    except mysql.connector.Error as err:
        print("Error fetching teacher assignments:", err)
        return jsonify({'success': False, 'message': 'Error fetching assignments'}), 500
    finally:
        cursor.close()
        connection.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# API endpoint to submit assignment
@app.route('/api/submit-assignment', methods=['POST'])
def submit_assignment():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['file']
    assignment_id = request.form.get('AssignmentID')
    srn = request.form.get('SRN')

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Secure the filename and open the file as binary data
        filename = secure_filename(file.filename)

        try:
            # Read the file as binary
            file_data = file.read()

            # Create a database connection
            connection = get_db_connection()
            cursor = connection.cursor()

            # Insert the file, assignment ID, SRN, and timestamp into the submissions table
            cursor.execute("""
                INSERT INTO submissions (SRN, AssignmentID, FileSubmitted, SubmissionDate, status)
                VALUES (%s, %s, %s, NOW(), 'Pending')
            """, (srn, assignment_id, file_data))

            connection.commit()

            # Close cursor and connection
            cursor.close()
            connection.close()

            return jsonify({'success': True, 'message': 'Assignment submitted successfully!'}), 200
        except mysql.connector.Error as err:
            print(f"Error saving file in DB: {err}")
            return jsonify({'success': False, 'message': 'Error saving file in database'}), 500
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500
    else:
        return jsonify({'success': False, 'message': 'File type not allowed'}), 400

@app.route('/api/add-assignment', methods=['POST'])
def add_assignment():
    data = request.get_json()

    # Extract form data from the request
    description = data.get('description')
    total_marks = data.get('totalMarks')
    date_of_submission = data.get('dateOfSubmission')
    course_id = data.get('courseId')

    if not description or not total_marks or not date_of_submission or not course_id:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert the new assignment into the database
        cursor.execute("""
            INSERT INTO assignments (CourseID, Description, TotalMarks, DateOfSubmission)
            VALUES (%s, %s, %s, %s)
        """, (course_id, description, total_marks, date_of_submission))

        # Commit the changes
        connection.commit()

        return jsonify({'success': True, 'message': 'Assignment added successfully'}), 200

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'success': False, 'message': 'Error adding assignment'}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)
