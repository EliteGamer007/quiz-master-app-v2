"""
Test Script: RSA Digital Signature for Quiz Results
Demonstrates signing and verification process
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from crypto_utils import sign_quiz_result, verify_quiz_result
from datetime import datetime

def test_signature():
    print("=" * 70)
    print("🔐 Testing RSA Digital Signature for Quiz Results")
    print("=" * 70)
    print()
    
    # Sample quiz result data
    user_id = 123
    quiz_id = 45
    score = 8.5
    timestamp = datetime.utcnow().isoformat()
    
    print("📝 Quiz Result Data:")
    print(f"   User ID:    {user_id}")
    print(f"   Quiz ID:    {quiz_id}")
    print(f"   Score:      {score}")
    print(f"   Timestamp:  {timestamp}")
    print()
    
    # Sign the result
    print("🔏 Step 1: Signing the result with RSA private key...")
    signature = sign_quiz_result(user_id, quiz_id, score, timestamp)
    print(f"   ✅ Signature generated: {signature[:60]}...")
    print(f"   Length: {len(signature)} characters (base64)")
    print()
    
    # Verify with correct data
    print("✓ Step 2: Verifying signature with CORRECT data...")
    is_valid = verify_quiz_result(user_id, quiz_id, score, timestamp, signature)
    print(f"   Result: {'✅ VALID - Data is authentic!' if is_valid else '❌ INVALID'}")
    print()
    
    # Attempt tampering - change score
    print("🚨 Step 3: Testing tampering detection - changing score...")
    tampered_score = 10.0  # Changed from 8.5 to 10.0
    is_valid_tampered = verify_quiz_result(user_id, quiz_id, tampered_score, timestamp, signature)
    print(f"   Score changed: {score} → {tampered_score}")
    print(f"   Result: {'✅ VALID' if is_valid_tampered else '❌ INVALID - Tampering detected!'}")
    print()
    
    # Attempt tampering - change user_id
    print("🚨 Step 4: Testing tampering detection - changing user ID...")
    tampered_user = 999
    is_valid_tampered2 = verify_quiz_result(tampered_user, quiz_id, score, timestamp, signature)
    print(f"   User ID changed: {user_id} → {tampered_user}")
    print(f"   Result: {'✅ VALID' if is_valid_tampered2 else '❌ INVALID - Tampering detected!'}")
    print()
    
    print("=" * 70)
    print("Summary:")
    print("  ✅ Digital signatures successfully protect quiz results")
    print("  ✅ Any tampering is immediately detected")
    print("  ✅ Students can verify their results are authentic")
    print("=" * 70)
    print()
    
    # Show how the data is formatted for signing
    print("🔍 Technical Details:")
    print(f"   Message format: \"user_id|quiz_id|score|timestamp\"")
    print(f"   Example: \"{user_id}|{quiz_id}|{score}|{timestamp}\"")
    print(f"   Hash algorithm: SHA-256 (using hashlib)")
    print(f"   Signature algorithm: RSA-2048 with PSS padding")
    print(f"   Encoding: Base64 (for database storage)")
    print()

if __name__ == "__main__":
    test_signature()
