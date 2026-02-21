/**
 * Vulnerable REST API Server
 * Demonstrates: XSS, Prototype Pollution, Weak JWT, NoSQL Injection,
 * Path Traversal, ReDOS, Insecure Dependencies
 */
const express = require('express');
const jwt = require('jsonwebtoken');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const crypto = require('crypto');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ─── Hardcoded Secrets ───────────────────────────
const JWT_SECRET = 'secret123';  // VULNERABLE: Weak, hardcoded JWT secret
const ADMIN_PASSWORD = 'admin123';
const DB_CONNECTION = 'mongodb://root:toor@prod-db:27017/myapp';
const PRIVATE_KEY = `-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGXZGUJRBJm2yVFF+VEv
-----END RSA PRIVATE KEY-----`;

// In-memory "database"
let users = {};
let posts = {};

// ─── Weak JWT Authentication ─────────────────────
app.post('/api/auth/login', (req, res) => {
    const { username, password } = req.body;
    // VULNERABLE: No password hashing, weak JWT secret, no expiration
    const token = jwt.sign(
        { username, role: 'user', isAdmin: false },
        JWT_SECRET
        // Missing: { expiresIn: '1h' }
    );
    res.json({ token });
});

// VULNERABLE: JWT verification with algorithm confusion
app.get('/api/auth/verify', (req, res) => {
    const token = req.headers.authorization?.split(' ')[1];
    try {
        // VULNERABLE: algorithms not specified — allows 'none' algorithm attack
        const decoded = jwt.verify(token, JWT_SECRET);
        res.json({ valid: true, user: decoded });
    } catch (e) {
        res.status(401).json({ valid: false });
    }
});

// ─── Reflected XSS ──────────────────────────────
app.get('/search', (req, res) => {
    const query = req.query.q;
    // VULNERABLE: User input reflected directly in HTML response
    res.send(`<html><body><h1>Search Results for: ${query}</h1></body></html>`);
});

app.get('/error', (req, res) => {
    const msg = req.query.message;
    // VULNERABLE: Error message reflects user input
    res.send(`<div class="error">Error: ${msg}</div>`);
});

// ─── Prototype Pollution ─────────────────────────
app.put('/api/users/:id/settings', (req, res) => {
    const userId = req.params.id;
    const settings = req.body;

    if (!users[userId]) {
        users[userId] = { settings: {} };
    }

    // VULNERABLE: Deep merge without __proto__ check — prototype pollution
    function deepMerge(target, source) {
        for (const key in source) {
            if (typeof source[key] === 'object' && source[key] !== null) {
                if (!target[key]) target[key] = {};
                deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        }
        return target;
    }

    deepMerge(users[userId].settings, settings);
    res.json({ success: true, settings: users[userId].settings });
});

// ─── NoSQL Injection ─────────────────────────────
app.post('/api/users/find', (req, res) => {
    const { username, password } = req.body;
    // VULNERABLE: Direct user input in query — NoSQL injection
    // Attacker can send: {"username": {"$gt": ""}, "password": {"$gt": ""}}
    const user = Object.values(users).find(
        u => u.username === username && u.password === password
    );
    res.json({ found: !!user, user });
});

// ─── Path Traversal ─────────────────────────────
app.get('/api/files/download', (req, res) => {
    const filename = req.query.name;
    // VULNERABLE: No path sanitization — directory traversal
    const filePath = path.join(__dirname, 'uploads', filename);
    res.sendFile(filePath);
});

app.get('/api/templates/:name', (req, res) => {
    // VULNERABLE: Path traversal via route parameter
    const templatePath = `./templates/${req.params.name}`;
    const content = fs.readFileSync(templatePath, 'utf8');
    res.send(content);
});

// ─── Command Injection ──────────────────────────
app.get('/api/system/ping', (req, res) => {
    const host = req.query.host;
    // VULNERABLE: Command injection via unsanitized input to exec
    exec(`ping -c 3 ${host}`, (error, stdout, stderr) => {
        res.json({ output: stdout, error: stderr });
    });
});

app.post('/api/files/convert', (req, res) => {
    const { inputFile, outputFormat } = req.body;
    // VULNERABLE: Command injection through file conversion
    exec(`convert ${inputFile} output.${outputFormat}`, (error, stdout) => {
        res.json({ success: !error, output: stdout });
    });
});

// ─── Insecure File Upload ───────────────────────
app.post('/api/upload', (req, res) => {
    const { filename, content } = req.body;
    // VULNERABLE: No file type validation, no size limits, no filename sanitization
    const uploadPath = path.join(__dirname, 'uploads', filename);
    fs.writeFileSync(uploadPath, Buffer.from(content, 'base64'));
    res.json({ path: uploadPath });
});

// ─── Information Disclosure ─────────────────────
app.get('/api/debug/env', (req, res) => {
    // VULNERABLE: Exposes environment variables including secrets
    res.json(process.env);
});

app.get('/api/debug/config', (req, res) => {
    // VULNERABLE: Exposes internal configuration
    res.json({
        dbConnection: DB_CONNECTION,
        jwtSecret: JWT_SECRET,
        adminPassword: ADMIN_PASSWORD,
        nodeVersion: process.version,
        platform: process.platform,
        memoryUsage: process.memoryUsage()
    });
});

// ─── Missing Rate Limiting ──────────────────────
app.post('/api/auth/reset-password', (req, res) => {
    // VULNERABLE: No rate limiting — allows brute force attacks
    const { email, newPassword } = req.body;
    // Process password reset without any throttling
    res.json({ success: true, message: 'Password reset' });
});

// ─── Insecure CORS ──────────────────────────────
app.use((req, res, next) => {
    // VULNERABLE: Wildcard CORS allows any origin
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', '*');
    res.setHeader('Access-Control-Allow-Headers', '*');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    next();
});

// ─── ReDoS (Regular Expression Denial of Service) ─
app.post('/api/validate/email', (req, res) => {
    const { email } = req.body;
    // VULNERABLE: Catastrophic backtracking regex
    const emailRegex = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    const isValid = emailRegex.test(email);
    res.json({ valid: isValid });
});

// ─── Insecure Random ────────────────────────────
app.get('/api/auth/generate-token', (req, res) => {
    // VULNERABLE: Math.random() is not cryptographically secure
    const token = Math.random().toString(36).substring(2);
    res.json({ token });
});

app.listen(3001, '0.0.0.0', () => {
    console.log('API Server running on port 3001');
});
