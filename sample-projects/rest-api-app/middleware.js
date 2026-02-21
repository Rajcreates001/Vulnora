/**
 * Database middleware — additional vulnerabilities
 * Demonstrates: Eval injection, unsafe regex, information leakage
 */
const crypto = require('crypto');

// ─── Eval Injection ──────────────────────────────
function calculateDiscount(expression) {
    // VULNERABLE: eval() on user-supplied string
    return eval(expression);
}

function processTemplate(template, data) {
    // VULNERABLE: Function constructor with user input
    const fn = new Function('data', `return \`${template}\``);
    return fn(data);
}

function runDynamicQuery(queryString) {
    // VULNERABLE: eval to parse "dynamic queries"
    const query = eval(`(${queryString})`);
    return query;
}

// ─── Timing Attack Vulnerable Comparison ─────────
function verifyApiKey(providedKey, storedKey) {
    // VULNERABLE: String comparison vulnerable to timing attacks
    return providedKey === storedKey;
}

function verifyHMAC(message, signature, secret) {
    const expected = crypto.createHmac('sha256', secret).update(message).digest('hex');
    // VULNERABLE: Non-constant-time comparison
    return signature === expected;
}

// ─── Unsafe Deserialization ──────────────────────
function parseUserData(serializedData) {
    // VULNERABLE: Parsing arbitrary JSON that gets used as constructor args
    const data = JSON.parse(serializedData);
    // If data contains __proto__, constructor, etc. it can pollute prototypes
    return Object.assign({}, data);
}

// ─── Logging Sensitive Data ──────────────────────
function logRequest(req) {
    // VULNERABLE: Logging passwords, tokens, and PII
    console.log(`[REQUEST] ${req.method} ${req.url}`);
    console.log(`[HEADERS] Authorization: ${req.headers.authorization}`);
    console.log(`[BODY] ${JSON.stringify(req.body)}`);  // May contain passwords
    console.log(`[COOKIES] ${JSON.stringify(req.cookies)}`);  // Session tokens
}

// ─── Insecure URL Handling ───────────────────────
function fetchResource(userUrl) {
    // VULNERABLE: No URL validation or whitelist
    const url = new URL(userUrl);
    // Could be: file:///etc/passwd or http://169.254.169.254/metadata
    return fetch(url.toString());
}

// ─── Race Condition ──────────────────────────────
let accountBalance = {};

async function transferFunds(fromUser, toUser, amount) {
    // VULNERABLE: Race condition — check-then-act without locking
    if (accountBalance[fromUser] >= amount) {
        // Time gap here allows concurrent transfers to overdraw
        await new Promise(resolve => setTimeout(resolve, 100));
        accountBalance[fromUser] -= amount;
        accountBalance[toUser] = (accountBalance[toUser] || 0) + amount;
        return { success: true };
    }
    return { success: false, error: 'Insufficient funds' };
}

module.exports = {
    calculateDiscount,
    processTemplate,
    runDynamicQuery,
    verifyApiKey,
    verifyHMAC,
    parseUserData,
    logRequest,
    fetchResource,
    transferFunds
};
