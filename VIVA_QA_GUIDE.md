# 📚 VIVA Q&A - Quick Reference Guide

## 🎯 Common Evaluator Questions & Answers

### 1. AUTHENTICATION

**Q: What hashing algorithm do you use for passwords?**
**A:** scrypt (memory-hard function) with parameters n=32768, r=8, p=1. Modern Werkzeug 3.x uses this by default. It's better than PBKDF2 because it's memory-hard, which resists GPU and ASIC-based brute force attacks.

**Q: Why do you need salt in password hashing?**
**A:** Salt ensures the same password produces different hashes for different users. This prevents rainbow table attacks (pre-computed hash lookups) and makes each user's password independently secure.

**Q: What is Multi-Factor Authentication and how did you implement it?**
**A:** MFA requires multiple forms of verification. We use:
- Factor 1: Password (something you know)
- Factor 2: Email OTP (something you have)
The OTP is 6 digits, valid for 5 minutes, and can only be used once.

**Q: Why OTP for users but not for admins/quiz masters?**
**A:** 
- Users have personal data (scores, attempts) → Need extra protection
- Quiz Masters only create content, no user data access → Password sufficient
- Admin is trusted system operator → Password sufficient

---

### 2. AUTHORIZATION (ACCESS CONTROL)

**Q: What Access Control model did you use?**
**A:** Role-Based Access Control (RBAC) with Access Control Matrix having 3 subjects (User, Quiz Master, Admin) and 7+ objects (Subjects, Chapters, Quizzes, Questions, Users, Scores, Analytics).

**Q: How do you enforce access control programmatically?**
**A:** Three ways:
1. **Decorators**: `@admin_required`, `@user_required`, `@quiz_master_required` on routes
2. **JWT tokens**: Store role in token claims, verify on each request
3. **Database filters**: `Quiz.query.filter_by(created_by_quiz_master_id=qm_id)` ensures ownership

**Q: Why can't Quiz Masters access user data?**
**A:** Separation of duties and privacy protection. Quiz Masters create content, they don't need to see who takes quizzes. This follows principle of least privilege.

**Q: What happens if a Quiz Master tries to edit another Quiz Master's quiz?**
**A:** Returns 404 Not Found. The database query filters by both quiz ID and ownership:
```python
Quiz.query.filter_by(id=quiz_id, created_by_quiz_master_id=current_qm_id).first_or_404()
```

---

### 3. ENCRYPTION

**Q: Why AES-256 and not RSA for correct answers?**
**A:** 
- **AES-256**: Symmetric, fast, efficient for bulk data encryption
- **RSA-2048**: Asymmetric, slow, limited data size (max 256 bytes)
For encrypting many answers repeatedly, AES is the right choice. RSA is used for signatures only.

**Q: What is CBC mode and why random IV?**
**A:** 
- **CBC (Cipher Block Chaining)**: Each block depends on previous block, provides better security than ECB
- **Random IV**: Ensures same plaintext produces different ciphertext each time, prevents pattern analysis

**Q: Where is the AES key stored?**
**A:** 
- **Production**: Environment variable `QUIZ_AES_KEY` (never in code/database)
- **Development**: Auto-generated in `keys/aes_key.bin` (gitignored)

**Q: What is PKCS7 padding?**
**A:** AES requires data to be multiple of 16 bytes. PKCS7 adds padding bytes (value = padding length) to reach block size. Example: "A" (1 byte) + 15 padding bytes = 16 bytes.

**Q: Client-side: Does the user ever see the correct answer?**
**A:** NO. 
- During quiz: Only question text and options (A/B/C/D) sent, NOT correct answer
- After submission: Only score returned, NOT which answers were correct
- Decryption happens only server-side during scoring

---

### 4. HASHING & DIGITAL SIGNATURES

**Q: Why use hashing before signing with RSA?**
**A:** Two reasons:
1. **Size limit**: RSA can only sign data smaller than key size. SHA-256 always produces 32 bytes
2. **Performance**: Hashing is fast, signing is slow. Hash once, sign the hash

**Q: What is SHA-256?**
**A:** Secure Hash Algorithm producing 256-bit (32-byte) digest. Properties:
- One-way: Can't reverse hash to get original data
- Deterministic: Same input always produces same hash
- Avalanche effect: Tiny input change = completely different hash

**Q: What gets signed in your digital signature?**
**A:** The message string: `user_id|quiz_id|score|timestamp`
Example: `"123|45|8.5|2026-01-27T10:30:00"`

**Q: How does signature prevent tampering?**
**A:** 
1. Any change to user_id, quiz_id, score, or timestamp changes the hash
2. Changed hash makes signature verification fail
3. Attacker can't create new valid signature (requires private key)

**Q: What is PSS padding in RSA?**
**A:** Probabilistic Signature Scheme - adds randomness to RSA signature for better security. More resistant to certain cryptographic attacks than older PKCS#1 v1.5.

---

### 5. ENCODING

**Q: What's the difference between encoding and encryption?**
**A:** 
- **Encoding** (Base64, Hex): Format conversion, reversible by anyone, NO security
- **Encryption** (AES, RSA): Protection, requires secret key to reverse, provides security

**Q: Why use Base64 if it's not secure?**
**A:** Base64 is NOT for security, it's for **data transfer**:
- Binary data can't be in JSON/URLs/emails
- Base64 converts binary to text (A-Z, a-z, 0-9, +, /)
- We use it to encode already-signed signatures for storage

**Q: Why hexadecimal for integrity hashes?**
**A:** Hexadecimal (0-9, a-f) is:
- **Human-readable**: Easy to compare visually
- **Standard**: Universally used for hashes (MD5, SHA-256)
- **Logging-friendly**: Good for debug output and logs

**Q: How does integrity hash detect tampering?**
**A:** 
1. Generate hash of quiz content at creation
2. Store hash in database
3. Before serving quiz, regenerate hash and compare
4. If hashes don't match → content was modified → alert!

---

### 6. SECURITY ATTACKS & MITIGATIONS

**Q: What is a rainbow table attack?**
**A:** Pre-computed table of hash → password mappings. Attacker looks up hash in table to find password instantly.
**Mitigation:** Salt makes each password hash unique, rainbow tables become useless.

**Q: What is SQL injection and how do you prevent it?**
**A:** Malicious SQL in user input: `admin'--` could bypass authentication.
**Mitigation:** SQLAlchemy ORM with parameterized queries, never concatenating user input into SQL.

**Q: What is a replay attack?**
**A:** Attacker captures valid OTP and reuses it later.
**Mitigation:** OTP expires in 5 minutes, used only once (cleared after verification).

**Q: What if database is stolen?**
**A:** 
- ✅ Passwords: Hashed with scrypt → Can't reverse
- ✅ Correct answers: AES encrypted → Can't decrypt without key
- ✅ Signatures: Still valid → Can verify authenticity
- ❌ Question text, options: Plaintext (not sensitive)

**Q: What is Man-in-the-Middle attack?**
**A:** Attacker intercepts communication between client and server.
**Mitigation:** 
- Production: HTTPS (TLS encryption) for all traffic
- JWT tokens: Signed, can't be modified
- OTP: One-time use, short expiry

---

### 7. CRYPTOGRAPHIC STRENGTH

**Q: Why RSA-2048 and not RSA-1024?**
**A:** RSA-1024 is deprecated (breakable with enough resources). RSA-2048 is current standard, recommended by NIST until 2030.

**Q: Why AES-256 and not AES-128?**
**A:** Both are secure, but AES-256 has larger key space (2^256 vs 2^128). Industry standard for sensitive data, required by US government for TOP SECRET data.

**Q: How strong is scrypt against brute force?**
**A:** Parameters n=32768, r=8, p=1 make each hash attempt require significant memory and CPU. GPU/ASIC attacks become impractical. Estimated ~10,000x slower than MD5.

---

### 8. DATABASE & ARCHITECTURE

**Q: Show me a question in the database - is the answer encrypted?**
**A:** 
```bash
cd Backend
python quick_demo.py
```
See section 8️⃣ - shows encrypted answer from actual database.

**Q: How do you prevent users from seeing correct answers in API response?**
**A:** In `user_routes.py`, the `correct_option` field is explicitly excluded:
```python
# 🔒 SECURITY: correct_option is NOT sent to client
'options': [q.option_a, q.option_b, q.option_c, q.option_d]
# correct_option field is never included
```

**Q: What happens during quiz submission?**
**A:** 
1. User sends answers: `{"1": "A", "2": "C"}`
2. Server fetches encrypted correct answers from DB
3. Server decrypts each answer: `decrypt_answer(question.correct_option)`
4. Server compares: `user_answer == decrypted_correct`
5. Server returns score only (not correct answers)

---

### 9. NIST SP 800-63-2 COMPLIANCE

**Q: What is NIST SP 800-63-2?**
**A:** NIST Special Publication 800-63-2: Electronic Authentication Guideline. Defines levels of authentication assurance.

**Q: What level does your application meet?**
**A:** 
- **Level 1**: Password authentication (single-factor)
- **Level 2**: Multi-factor authentication (password + OTP)

**Q: What is E-Authentication Architecture?**
**A:** Framework for secure authentication systems:
1. **Credential Service Provider**: Issues and manages credentials (password hashing)
2. **Verifier**: Validates credentials (password check + OTP verification)
3. **Relying Party**: Application trusting authentication (backend API)

---

## 🚀 DEMONSTRATION COMMANDS

### Single Command - All Features
```bash
cd Backend
python quick_demo.py
```

### Comprehensive Tests - All 85 Tests
```bash
cd Backend
python test_security_comprehensive.py
```

---

## 📊 MARKS ALLOCATION CHECKLIST

| Component | Implementation | Marks | Status |
|-----------|----------------|-------|--------|
| **Authentication** | Password (scrypt + salt) + MFA (OTP) | 3 | ✅ |
| **Authorization** | RBAC with ACM (3×7+) + Decorators | 3 | ✅ |
| **Encryption** | RSA-2048 + AES-256-CBC | 3 | ✅ |
| **Hashing** | scrypt + SHA-256 + RSA signature | 3 | ✅ |
| **Encoding** | Base64 + Hex + Theory | 3 | ✅ |
| **TOTAL** | | **15** | ✅ |

---

**Best of luck for your viva! 🎓**
