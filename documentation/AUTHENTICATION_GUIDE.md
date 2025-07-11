# Authentication Guide

## Overview

The Metadata Builder includes a complete multi-user authentication system with JWT-based security, user management, and role-based access control.

## 🔐 Authentication Architecture

### Backend Components
- **JWT Authentication**: Secure token-based authentication
- **User Management**: Database-backed user accounts with roles
- **Session Management**: Encrypted session storage for connection credentials
- **Password Security**: bcrypt hashing with salt
- **Role-Based Access**: Admin and user roles with different permissions

### Database Schema
All authentication data is stored in the `metadata_builder` schema:
- `users` - User accounts and profiles
- `user_connections` - User-specific database connections
- `system_connections` - Admin-managed shared connections
- `user_sessions` - Active user sessions
- `connection_audit` - Security audit logs
- `metadata_jobs` - User-specific background jobs

## 🚀 API Endpoints

### Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "3af21da7-4cd4-4598-af41-c588ae02cfe3",
    "username": "admin",
    "email": "admin@metadata-builder.com",
    "role": "admin",
    "is_active": true
  }
}
```

#### Register New User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Get Current User Info
```http
GET /api/v1/auth/me
Authorization: Bearer <jwt_token>
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <jwt_token>
```

#### Validate Token
```http
GET /api/v1/auth/validate
Authorization: Bearer <jwt_token>
```

### Authenticated Endpoints

All database and metadata endpoints require authentication:

```http
Authorization: Bearer <jwt_token>
```

**Protected endpoints:**
- `/api/v1/database/connections` - Database connection management
- `/api/v1/metadata/generate` - Metadata generation
- `/api/v1/agent/chat` - AI chat interface

## 🔑 Default Credentials

**Admin Account:**
- Username: `admin`
- Email: `admin@metadata-builder.com`
- Password: `admin123`
- Role: `admin`

⚠️ **IMPORTANT**: Change the default password immediately in production!

## 🌐 Frontend Integration

### JavaScript/React Authentication Helper

```javascript
class AuthService {
  constructor() {
    this.baseURL = 'http://localhost:8000/api/v1';
    this.token = localStorage.getItem('auth_token');
  }

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
      localStorage.setItem('auth_token', this.token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      return data;
    } else {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }
  }

  async logout() {
    if (this.token) {
      await fetch(`${this.baseURL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      });
    }
    
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }

  getAuthHeaders() {
    return this.token ? {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    } : {
      'Content-Type': 'application/json',
    };
  }

  isAuthenticated() {
    return !!this.token;
  }

  getCurrentUser() {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : null;
  }

  async validateToken() {
    if (!this.token) return false;
    
    try {
      const response = await fetch(`${this.baseURL}/auth/validate`, {
        headers: { 'Authorization': `Bearer ${this.token}` },
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Usage
const auth = new AuthService();
export default auth;
```

### API Client with Authentication

```javascript
class APIClient {
  constructor(authService) {
    this.auth = authService;
    this.baseURL = 'http://localhost:8000/api/v1';
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.auth.getAuthHeaders(),
      ...options,
    };

    const response = await fetch(url, config);
    
    if (response.status === 401) {
      // Token expired or invalid
      this.auth.logout();
      window.location.href = '/login';
      return;
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // Database connections
  async getConnections() {
    return this.request('/database/connections');
  }

  async createConnection(connectionData) {
    return this.request('/database/connections', {
      method: 'POST',
      body: JSON.stringify(connectionData),
    });
  }

  async testConnection(connectionName) {
    return this.request(`/database/connections/${connectionName}/test`, {
      method: 'POST',
    });
  }

  // Schema browsing
  async getSchemas(connectionName) {
    return this.request(`/database/connections/${connectionName}/schemas`);
  }
}
```

## 🛡️ Security Features

### Password Requirements
- Minimum 8 characters
- Must contain uppercase, lowercase, and numeric characters
- bcrypt hashing with salt

### JWT Token Security
- 24-hour expiration (configurable)
- HS256 algorithm
- Includes user ID, username, and role
- Secure secret key (configurable via environment)

### Session Management
- Encrypted credential storage
- Automatic session cleanup
- IP address and user agent tracking

### Audit Logging
All connection operations are logged:
- Connection attempts (success/failure)
- Schema browsing
- Metadata generation
- IP address and timestamp tracking

## 🔧 Configuration

### Environment Variables

```bash
# Authentication settings
JWT_SECRET_KEY=your-secure-jwt-secret-key
SESSION_ENCRYPTION_KEY=your-32-byte-encryption-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database settings for auth schema
DATABASE_URL=postgresql://username:password@localhost:5432/database
AUTH_SCHEMA=metadata_builder
```

### Password Security

```python
# In scripts/setup_auth.py
from metadata_builder.auth.auth_utils import PasswordUtils

# Hash password
hashed = PasswordUtils.hash_password("my_secure_password")

# Verify password
is_valid = PasswordUtils.verify_password("my_secure_password", hashed)
```

## 🔄 User Workflow

### 1. Initial Setup
```bash
# Create auth tables
python scripts/create_user_tables.py

# Validate setup
python scripts/validate_schema_setup.py
```

### 2. User Registration/Login
```javascript
// Login existing user
const loginData = await auth.login('admin', 'admin123');

// Register new user
const response = await fetch('/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'newuser',
    email: 'user@example.com',
    password: 'securepass',
    first_name: 'John',
    last_name: 'Doe'
  })
});
```

### 3. Database Connection Management
```javascript
// Create user connection
await apiClient.createConnection({
  name: 'my_database',
  type: 'postgresql',
  host: 'localhost',
  port: 5432,
  username: 'dbuser',
  password: 'dbpass',
  database: 'mydb'
});

// Test connection
const testResult = await apiClient.testConnection('my_database');
console.log(testResult.status); // 'success' or 'failed'
```

### 4. Schema Exploration
```javascript
// Browse database schemas
const schemas = await apiClient.getSchemas('my_database');
schemas.schemas.forEach(schema => {
  console.log(`Schema: ${schema.schema_name}`);
  console.log(`Tables: ${schema.tables.join(', ')}`);
});
```

## 🚨 Troubleshooting

### Common Issues

**Login fails with "Login failed":**
- Check username/email and password
- Verify user is active in database
- Check server logs for details

**Token validation fails:**
- Token may have expired (24 hours default)
- JWT secret key mismatch
- Re-login to get new token

**Connection creation fails:**
- Ensure user is authenticated
- Check database connection permissions
- Verify connection parameters

**Schema browsing returns empty:**
- Verify database connection is working
- Check database user permissions
- Ensure connection name exists

### Debug Commands

```bash
# Check user exists
python -c "
from metadata_builder.auth.models import User
from metadata_builder.auth.auth_utils import get_database_session
db = next(get_database_session())
user = db.query(User).filter(User.username == 'admin').first()
print(f'User: {user.username if user else \"Not found\"}')
"

# Test password verification
python -c "
from metadata_builder.auth.auth_utils import PasswordUtils
print(PasswordUtils.verify_password('admin123', 'stored_hash_here'))
"

# Validate JWT token
python -c "
from metadata_builder.auth.auth_utils import verify_token
user_id = verify_token('jwt_token_here')
print(f'User ID: {user_id}')
"
```

## 🎯 Next Steps

1. **Frontend Integration**: Implement login/logout components
2. **Role-Based UI**: Show/hide features based on user role
3. **Session Persistence**: Auto-login with valid tokens
4. **Password Reset**: Email-based password recovery
5. **User Management UI**: Admin interface for user management
6. **Advanced Security**: 2FA, session limits, etc. 