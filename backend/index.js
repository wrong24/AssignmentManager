const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const crypto = require('crypto');  // Use crypto for SHA-256 hashing
const db = require('./db');

const app = express(); 
const PORT = 5000;

app.use(cors());
app.use(bodyParser.json());

// Register Route (Student)
app.post('/api/student-register', async (req, res) => {
  const { id, name, email, branch, password } = req.body;
  console.log('Student register endpoint hit');

  // Hash password using SHA-256
  const hashedPassword = crypto.createHash('sha256').update(password).digest('hex');

  const query = 'INSERT INTO student (SRN, Name, Email, Branch, Password) VALUES (?, ?, ?, ?, ?)';
  db.query(query, [id, name, email, branch, hashedPassword], (err, result) => {
    if (err) {
      console.error('Error registering student:', err);
      res.status(500).json({ success: false, message: 'Registration failed' });
    } else {
      res.status(200).json({ success: true, message: 'Student registered successfully' });
    }
  });
});

// Register Route (Teacher)
app.post('/api/teacher-register', async (req, res) => {
  const { id, name, email, password } = req.body;

  // Hash password using SHA-256
  const hashedPassword = crypto.createHash('sha256').update(password).digest('hex');

  const query = 'INSERT INTO teacher (TRN, Name, Email, Password) VALUES (?, ?, ?, ?)';
  db.query(query, [id, name, email, hashedPassword], (err, result) => {
    if (err) {
      console.error('Error registering teacher:', err);
      res.status(500).json({ success: false, message: 'Registration failed' });
    } else {
      res.status(200).json({ success: true, message: 'Teacher registered successfully' });
    }
  });
});

// Login Route (Student)
app.post('/api/student-login', async (req, res) => {
  const { id, password } = req.body;
  const hashedPassword = crypto.createHash('sha256').update(password).digest('hex');
  
  const query = 'SELECT * FROM student WHERE SRN = ? AND Password = ?';
  db.query(query, [id, hashedPassword], (error, results) => {
    if (error) {
      console.error('Error fetching student:', error);
      res.status(500).json({ success: false, message: 'Database error' });
    } else if (results.length > 0) {
      res.json({ success: true, message: 'Login successful' });
    } else {
      res.status(400).json({ success: false, message: 'Invalid ID or Password' });
    }
  });
});

// Login Route (Teacher)
app.post('/api/teacher-login', (req, res) => {
  const { id, password } = req.body;

  const query = 'SELECT * FROM teacher WHERE TRN = ?';
  db.query(query, [id], (err, results) => {
    if (err) {
      console.error('Error fetching teacher:', err);
      return res.status(500).json({ success: false, message: 'Login failed' });
    }

    if (results.length === 0) {
      return res.status(400).json({ success: false, message: 'Invalid ID or Password' });
    }

    const teacher = results[0];
    const hashedPassword = crypto.createHash('sha256').update(password).digest('hex');

    if (teacher.Password === hashedPassword) {
      res.status(200).json({ success: true, message: 'Login successful' });
    } else {
      res.status(400).json({ success: false, message: 'Invalid ID or Password' });
    }
  });
});

// Fetch Course Data
app.get('/api/courses', (req, res) => {
  const query = 'SELECT * FROM Course';
  db.query(query, (err, results) => {
    if (err) {
      console.error('Error fetching courses:', err);
      res.status(500).json({ success: false, message: 'Error fetching courses' });
    } else {
      res.status(200).json({ success: true, courses: results });
    }
  });
});

// Fetch Assignments and Marks
app.get('/api/assignments', (req, res) => {
  const query = `
    SELECT a.AssignmentName, a.Description, m.MarksAwarded, m.TotalMarks
    FROM Assignment a 
    JOIN Marks m ON a.AssignmentID = m.AssignmentID 
    WHERE m.StudentID = ?`;
  
  const studentId = req.query.studentId; // Assuming you pass studentId as a query param
  
  db.query(query, [studentId], (err, results) => {
    if (err) {
      console.error('Error fetching assignments:', err);
      res.status(500).json({ success: false, message: 'Error fetching assignments' });
    } else {
      res.status(200).json({ success: true, assignments: results });
    }
  });
});

// Submit Marks
app.post('/api/submit-marks', (req, res) => {
  const { studentId, assignmentId, marksAwarded } = req.body;

  const query = 'UPDATE Marks SET MarksAwarded = ? WHERE StudentID = ? AND AssignmentID = ?';
  db.query(query, [marksAwarded, studentId, assignmentId], (err, result) => {
    if (err) {
      console.error('Error updating marks:', err);
      res.status(500).json({ success: false, message: 'Error submitting marks' });
    } else {
      res.status(200).json({ success: true, message: 'Marks submitted successfully' });
    }
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
