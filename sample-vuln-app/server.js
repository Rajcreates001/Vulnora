// Sample vulnerable Express.js application for testing Vulnora.
// DO NOT deploy this in production.

const express = require("express");
const mysql = require("mysql");
const { exec } = require("child_process");
const fs = require("fs");
const jwt = require("jsonwebtoken");

const app = express();
app.use(express.json());

// VULN: Hardcoded credentials
const JWT_SECRET = "my-secret-token-123";
const DB_PASSWORD = "root_password";

const db = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: DB_PASSWORD,
  database: "myapp",
});

// VULN: SQL Injection
app.get("/api/users/:id", (req, res) => {
  const userId = req.params.id;
  const query = `SELECT * FROM users WHERE id = ${userId}`;
  db.query(query, (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

// VULN: Command Injection
app.post("/api/convert", (req, res) => {
  const { filename } = req.body;
  exec(`convert ${filename} output.pdf`, (err, stdout) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ output: stdout });
  });
});

// VULN: Path Traversal
app.get("/api/download", (req, res) => {
  const file = req.query.file;
  const filePath = `./uploads/${file}`;
  res.sendFile(filePath, { root: __dirname });
});

// VULN: XSS - reflecting user input
app.get("/api/search", (req, res) => {
  const q = req.query.q;
  res.send(`<html><body>Search results for: ${q}</body></html>`);
});

// VULN: Insecure JWT with no expiry
app.post("/api/login", (req, res) => {
  const { username, password } = req.body;
  // No password validation shown, weak JWT
  const token = jwt.sign({ username }, JWT_SECRET);
  res.json({ token });
});

// VULN: Prototype Pollution
app.post("/api/settings", (req, res) => {
  const settings = {};
  const userInput = req.body;
  // Merging untrusted input into object
  Object.keys(userInput).forEach((key) => {
    settings[key] = userInput[key];
  });
  res.json(settings);
});

// VULN: No rate limiting, no auth on sensitive endpoint
app.delete("/api/users/:id", (req, res) => {
  const userId = req.params.id;
  db.query(`DELETE FROM users WHERE id = ${userId}`, (err) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ deleted: true });
  });
});

// VULN: CORS wildcard
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "*");
  next();
});

app.listen(3001, () => console.log("Server on 3001"));
