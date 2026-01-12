"""
Initialize RSA Keys for Digital Signatures
Run this once to generate the key pair before starting the application
"""

import sys
import os

# Add Backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from crypto_utils import generate_rsa_keys

if __name__ == "__main__":
    print("=" * 60)
    print("RSA Key Pair Generation for Quiz Result Digital Signatures")
    print("=" * 60)
    print()
    print("This will generate:")
    print("  • Private Key (2048-bit) - Server uses this to SIGN results")
    print("  • Public Key - Students use this to VERIFY signatures")
    print()
    
    generate_rsa_keys()
    
    print()
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Keep private_key.pem SECURE (never share)")
    print("  2. Public key can be shared via /api/public-key endpoint")
    print("  3. Start your Flask application")
    print()
