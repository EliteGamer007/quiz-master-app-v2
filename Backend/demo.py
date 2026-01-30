"""
Quick Security Demo Script
Run: python quick_demo.py
Shows all security implementations in action
"""

print("=" * 70)
print(" QUIZ MASTER - SECURITY FEATURES DEMO")
print("=" * 70)
print()

# 1. PASSWORD HASHING WITH SALT
print("1️  PASSWORD HASHING (scrypt + salt)")
print("-" * 70)
from werkzeug.security import generate_password_hash, check_password_hash

password = "SecurePass123"
hash1 = generate_password_hash(password)
hash2 = generate_password_hash(password)

print(f"Original Password:  {password}")
print(f"Hash 1:            {hash1[:50]}...")
print(f"Hash 2:            {hash2[:50]}...")
print(f"Same password, different hashes? {hash1 != hash2}")
print(f" Correct password verifies:   {check_password_hash(hash1, password)}")
print(f" Wrong password fails:        {check_password_hash(hash1, 'WrongPass')}")
print()

# 2. AES-256 ENCRYPTION
print("2️  AES-256-CBC ENCRYPTION (Correct Answers)")
print("-" * 70)
from crypto_utils import encrypt_answer, decrypt_answer

answer = "A"
encrypted1 = encrypt_answer(answer)
encrypted2 = encrypt_answer(answer)
encrypted3 = encrypt_answer(answer)
decrypted = decrypt_answer(encrypted1)

print(f"Original Answer:   {answer}")
print(f"Encrypted 1:       {encrypted1}")
print(f"Encrypted 2:       {encrypted2}")
print(f"Encrypted 3:       {encrypted3}")
print(f"Same answer, different ciphertext (random IV)? {encrypted1 != encrypted2}")
print(f" Decrypts back to: {decrypted}")
print()

# 3. RSA DIGITAL SIGNATURES
print("3️  RSA-2048 DIGITAL SIGNATURES (SHA-256)")
print("-" * 70)
from crypto_utils import sign_quiz_result, verify_quiz_result

user_id, quiz_id, score, timestamp = 123, 45, 8.5, "2026-01-27T10:00:00"
signature = sign_quiz_result(user_id, quiz_id, score, timestamp)

print(f"Message: {user_id}|{quiz_id}|{score}|{timestamp}")
print(f"Signature: {signature[:60]}...")
print(f" Valid signature:   {verify_quiz_result(user_id, quiz_id, score, timestamp, signature)}")
print(f" Tampered user_id:  {verify_quiz_result(999, quiz_id, score, timestamp, signature)}")
print(f" Tampered score:    {verify_quiz_result(user_id, quiz_id, 10.0, timestamp, signature)}")
print()

# 4. BASE64 ENCODING
print("  BASE64 ENCODING (Verification Tokens)")
print("-" * 70)
from crypto_utils import encode_quiz_result_base64, decode_quiz_result_base64

token = encode_quiz_result_base64(user_id, quiz_id, score, timestamp)
decoded = decode_quiz_result_base64(token)

print(f"Original Data: user={user_id}, quiz={quiz_id}, score={score}")
print(f"Base64 Token:  {token}")
print(f"Decoded Data:  {decoded}")
print()

# 5. HEXADECIMAL ENCODING
print("  HEXADECIMAL ENCODING (Integrity Hashes)")
print("-" * 70)
from crypto_utils import generate_quiz_integrity_hex, verify_quiz_integrity_hex

quiz_id = 1
questions = "1:What is Python?:A|2:What is Flask?:B|3:What is SQL?:C"
integrity_hash = generate_quiz_integrity_hex(quiz_id, questions)

print(f"Quiz Content: {questions[:50]}...")
print(f"SHA-256 Hash: {integrity_hash}")
print(f" Valid integrity:  {verify_quiz_integrity_hex(quiz_id, questions, integrity_hash)}")
print(f" Tampered content: {verify_quiz_integrity_hex(quiz_id, '1:Tampered?:D', integrity_hash)}")
print()

# 6. OTP GENERATION
print("6️  OTP GENERATION (Multi-Factor Authentication)")
print("-" * 70)
from routes.auth_routes import generate_otp

otps = [generate_otp() for _ in range(5)]
print(f"Generated OTPs: {', '.join(otps)}")
print(f"All 6 digits?   {all(len(otp) == 6 for otp in otps)}")
print(f"All numeric?    {all(otp.isdigit() for otp in otps)}")
print(f"All unique?     {len(set(otps)) == len(otps)}")
print()

# 7. ACCESS CONTROL
print("7️  ACCESS CONTROL (Role-Based)")
print("-" * 70)
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'demo-secret'
jwt = JWTManager(app)

with app.app_context():
    admin_token = create_access_token(identity='admin')
    user_token = create_access_token(identity={'id': 1, 'role': 'user', 'email': 'user@test.com'})
    qm_token = create_access_token(identity={'id': 1, 'role': 'quiz_master', 'email': 'qm@test.com'})
    
    print(f"Admin Token:       {admin_token[:50]}...")
    print(f" User Token:        {user_token[:50]}...")
    print(f"Quiz Master Token: {qm_token[:50]}...")
print()

# 8. DATABASE ENCRYPTION CHECK
print(" DATABASE CHECK (Encrypted Answers)")
print("-" * 70)
from app import create_app
from models.models import Question

demo_app = create_app()
with demo_app.app_context():
    # Get first question
    question = Question.query.first()
    if question:
        print(f"Question ID:       {question.id}")
        print(f"Question Text:     {question.question_text[:60]}...")
        print(f"Encrypted Answer:  {question.correct_option[:50]}...")
        print(f"Answer Length:     {len(question.correct_option)} chars (Base64)")
        try:
            decrypted = decrypt_answer(question.correct_option)
            print(f"Decrypts to:      {decrypted}")
        except:
            print(f"Not encrypted or invalid format")
    else:
        print("No questions in database yet")
print()

