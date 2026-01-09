# Environment Setup Guide

## Quick Start

### 1. Configure Email (Required)

Edit `Backend/.env` file:
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 2. Get Gmail App Password

1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Search "App passwords"
4. Select **Mail** → **Other (Custom name)**
5. Copy the 16-character password
6. Paste into `.env` file

### 3. Install Dependencies

**Backend:**
```bash
cd Backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd Frontend
npm install
```

### 4. Start Application

**Terminal 1 - Backend:**
```bash
cd Backend
python app.py
```
Backend runs on: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd Frontend
npm run serve
```
Frontend runs on: http://localhost:8080 or http://localhost:8082

### 5. Test Login & Registration

**Register New User (with OTP):**
1. Go to http://localhost:8080/register
2. Fill in registration details
3. Click Register
4. Check email for 6-digit verification code
5. Enter OTP to complete registration
6. Success! You can now login

**User Login (with OTP):**
- Use registered account
- OTP will be sent to email

**Admin Login (No OTP):**
- Email: admin@quiz.com
- Password: admin123

## Environment Variables

The `.env` file is already configured with your credentials. It contains:

```
SECRET_KEY=super-secret-key-ig
JWT_SECRET_KEY=super-secret-key-jwt
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=sanjeevevps@gmail.com
MAIL_PASSWORD=oion jfgz vccv crvr
MAIL_DEFAULT_SENDER=sanjeevevps@gmail.com
```

**Note:** `.env` is in `.gitignore` for security. Never commit this file to git.

## Security Best Practices

✅ Email credentials secured in `.env` file
✅ `.env` added to `.gitignore`
✅ `.env.example` provided as template
✅ Environment variables loaded via python-dotenv
✅ OTP system with 5-minute expiration
✅ JWT-based authentication

## Troubleshooting

**"Failed to send OTP"**
- Check `.env` file exists in Backend folder
- Verify MAIL_PASSWORD is correct
- Ensure 2-Step Verification is enabled

**"Module not found"**
- Run: `pip install -r requirements.txt`

**"Email not received"**
- Check spam folder
- Verify email credentials in `.env`
- Test with different email address

## Production Checklist

Before deploying to production:

- [ ] Generate new SECRET_KEY and JWT_SECRET_KEY
- [ ] Use production email service (SendGrid, AWS SES)
- [ ] Switch from SQLite to PostgreSQL/MySQL
- [ ] Set DEBUG=False
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Set up backup system

## Application URLs

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: Check routes/ folder

## Support

For issues, check:
- ERRORLOG.md
- Backend terminal for errors
- Frontend console (F12)
- Application logs

---

**Ready to Go!** 🚀

Your application is fully configured and ready for use.
