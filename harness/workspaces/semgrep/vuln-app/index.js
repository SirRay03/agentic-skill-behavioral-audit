const express = require("express");
const mysql = require("mysql2");

const app = express();
const db = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: "root",
  database: "app",
});

app.get("/users/:id", (req, res) => {
  const id = req.params.id;
  db.query("SELECT * FROM users WHERE id=" + id, (err, rows) => {
    if (err) return res.status(500).send(err.message);
    res.json(rows);
  });
});

app.get("/search", (req, res) => {
  const q = req.query.q;
  db.query(`SELECT * FROM products WHERE name LIKE '%${q}%'`, (err, rows) => {
    if (err) return res.status(500).send(err.message);
    res.json(rows);
  });
});

app.listen(3000);
