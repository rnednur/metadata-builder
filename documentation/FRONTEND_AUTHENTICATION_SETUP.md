# Frontend Authentication Setup Guide

## 🎯 Overview

This guide covers setting up the frontend authentication system that integrates with the JWT-based backend authentication API.

## 🔧 Components Added

### 1. Authentication Service (`frontend/src/services/authService.js`)
- JWT token management (localStorage)
- Login/logout functionality
- User registration
- Token validation
- Auto-logout on token expiration

### 2. Login/Register Page (`frontend/src/pages/login/index.jsx`)
- Clean login form with username/password
- User registration form with validation
- Auto-redirect after successful login
- Default admin credentials display
- Error handling and loading states

### 3. Protected Route Component (`frontend/src/components/ProtectedRoute.jsx`)
- Guards protected pages from unauthenticated access
- Validates JWT tokens with backend
- Redirects to login with return URL preservation
- Loading spinner during authentication check

### 4. Updated Header Component (`frontend/src/components/ui/Header.jsx`)
- User profile dropdown with initials/avatar
- User info display (name, email, role)
- Logout functionality
- Click-outside menu closing

### 5. Updated API Service (`frontend/src/services/api.js`)
- Automatic JWT token injection in requests
- 401 error handling with auto-logout
- Seamless authentication flow

### 6. Updated Routes (`frontend/src/Routes.jsx`)
- Protected route wrapping for all authenticated pages
- Public login route
- Proper route organization

## 🚀 Quick Start

### 1. Test the Authentication Flow

1. **Start the frontend and backend:**
   ```bash
   # Terminal 1: Backend
   cd metadata-builder
   python -m uvicorn metadata_builder.api.app:app --host 0.0.0.0 --port 8000 --reload

   # Terminal 2: Frontend  
   cd frontend
   npm run dev
   ```

2. **Access the application:**
   - Visit: http://localhost:4028
   - Should redirect to: http://localhost:4028/login

3. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin123`
   - Should redirect to dashboard after successful login

### 2. Test User Registration

1. **Create a new user account:**
   - Click "Don't have an account? Register here"
   - Fill in user details:
     ```
     First Name: John
     Last Name: Doe
     Username: johndoe
     Email: john@example.com
     Password: securepass123
     ```
   - Click "Create account"
   - Should auto-login and redirect to dashboard

### 3. Test Authentication Features

1. **User Profile Menu:**
   - Click user avatar in top-right header
   - Should show user name, email, and role
   - Click "Sign out" to logout

2. **Protected Routes:**
   - Try accessing any page while logged out
   - Should redirect to login page
   - After login, should return to intended page

3. **Token Validation:**
   - Refresh the page while logged in
   - Should maintain login state
   - If token expires, should auto-logout

## 🔐 Security Features

### Token Management
- **Storage**: JWT tokens stored in localStorage
- **Expiration**: 24-hour token lifetime (configurable)
- **Validation**: Server-side token validation on each request
- **Auto-logout**: Automatic logout on token expiration or 401 errors

### Password Security
- **Frontend**: Basic client-side validation
- **Backend**: bcrypt hashing with salt
- **Requirements**: Configurable password complexity

### Session Management
- **Persistence**: Login state persists across page refreshes
- **Cleanup**: Automatic token cleanup on logout
- **Redirect**: Preserves intended destination after login

## 🎨 UI/UX Features

### Login Page
- **Clean Design**: Modern, centered login form
- **Dual Mode**: Toggle between login and registration
- **Validation**: Real-time form validation
- **Loading States**: Visual feedback during authentication
- **Error Handling**: Clear error messages

### Header Integration
- **User Avatar**: Displays user initials
- **Profile Info**: Shows name, email, and role
- **Dropdown Menu**: Smooth user menu interaction
- **Responsive**: Mobile-friendly design

### Protected Routes
- **Loading Spinner**: Shows during authentication check
- **Seamless Redirects**: Smooth navigation flow
- **Return URLs**: Preserves intended destination

## 🛠️ Customization

### 1. Update Default Credentials

**⚠️ IMPORTANT**: Change default admin password in production!

```python
# In scripts/create_user_tables.py or via database
UPDATE metadata_builder.users 
SET password_hash = '<new_bcrypt_hash>'
WHERE username = 'admin';
```

### 2. Configure Token Expiration

```javascript
// In backend: metadata_builder/config/config.yaml
auth:
  access_token_expire_minutes: 1440  # 24 hours

// Or via environment variable
ACCESS_TOKEN_EXPIRE_MINUTES=720  # 12 hours
```

### 3. Customize Login Page

```jsx
// In frontend/src/pages/login/index.jsx
// Modify form fields, styling, or validation
const LoginForm = () => (
  // Your customizations here
);
```

### 4. Add Role-Based Features

```jsx
// In any component
import authService from '../services/authService.js';

const MyComponent = () => {
  const user = authService.getUser();
  const isAdmin = authService.isAdmin();
  
  return (
    <div>
      {isAdmin && <AdminOnlyFeature />}
      {user.role === 'user' && <UserFeature />}
    </div>
  );
};
```

## 🐛 Troubleshooting

### Common Issues

**1. Login redirects to login page infinitely:**
- Check if backend authentication service is running
- Verify JWT_SECRET_KEY is set in backend environment
- Check browser console for API errors

**2. "Network Error" on login:**
- Verify backend is running on http://localhost:8000
- Check CORS settings in backend
- Confirm API endpoints are accessible

**3. User avatar shows "?" instead of initials:**
- Check if user data includes first_name and last_name
- Verify user registration is populating these fields
- Check authService.getCurrentUser() response

**4. Token validation fails:**
- Verify JWT_SECRET_KEY matches between sessions
- Check token expiration time
- Confirm database connection is working

### Debug Commands

```bash
# Check if user exists in database
python -c "
from metadata_builder.auth.models import User
from metadata_builder.auth.auth_utils import get_database_session
db = next(get_database_session())
user = db.query(User).filter(User.username == 'admin').first()
print(f'User found: {user.username if user else \"Not found\"}')
"

# Test JWT token creation
python -c "
from metadata_builder.auth.auth_utils import create_access_token
token = create_access_token({'user_id': 'test', 'username': 'test'})
print(f'Test token: {token[:50]}...')
"

# Verify API is accessible
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 🔄 Next Steps

1. **Password Reset**: Add email-based password recovery
2. **2FA**: Implement two-factor authentication
3. **Session Limits**: Limit concurrent sessions per user
4. **Audit Dashboard**: Admin interface for user management
5. **Role Management**: More granular permission system
6. **Remember Me**: Optional persistent login sessions

## 📱 Mobile Considerations

The authentication system is fully responsive and works on mobile devices:

- **Touch-friendly**: Large touch targets for buttons
- **Responsive Design**: Adapts to different screen sizes
- **Mobile Menu**: User menu works properly on mobile
- **Form Validation**: Mobile-friendly error messages

## 🔗 Integration with Existing Features

The authentication system integrates seamlessly with existing features:

- **Database Connections**: User-specific connections
- **Schema Explorer**: Access control per connection
- **Metadata Generation**: User-aware job tracking
- **AI Chat**: User-specific conversation history
- **Job Queue**: User-scoped background jobs

All existing API calls now automatically include authentication headers! 