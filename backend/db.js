const mysql = require('mysql2/promise'); // Import the promise-based version of mysql2

// Create a Promise-based connection pool
const db = mysql.createPool({
  host: '127.0.0.1',
  user: 'root',
  password: 'password',
  database: 'assignmentmanager'
});

module.exports = db;
