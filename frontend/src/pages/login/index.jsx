import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../../services/authService.js';
import { AppIcon } from '../../components/AppIcon.jsx';
import { Button } from '../../components/ui/Button.jsx';
import { Input } from '../../components/ui/Input.jsx';
import { ErrorBoundary } from '../../components/ErrorBoundary.jsx';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  
  const navigate = useNavigate();
  const location = useLocation();
  
  const from = location.state?.from?.pathname || '/';

  useEffect(() => {
    // If already authenticated, redirect to intended page
    if (authService.isAuthenticated()) {
      navigate(from, { replace: true });
    }
  }, [navigate, from]);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await authService.login(formData.username, formData.password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (registerData.password !== registerData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      const { confirmPassword, ...registrationData } = registerData;
      await authService.register(registrationData);
      setShowRegister(false);
      setError('');
      // Auto-login after registration
      await authService.login(registerData.username, registerData.password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

    const handleInputChange = React.useCallback((e, isRegister = false) => {
    const { name, value } = e.target;
    if (isRegister) {
      setRegisterData(prev => ({ ...prev, [name]: value }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  }, []);

  const handleLoginInputChange = React.useCallback((e) => {
    handleInputChange(e, false);
  }, [handleInputChange]);

  const handleRegisterInputChange = React.useCallback((e) => {
    handleInputChange(e, true);
  }, [handleInputChange]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <div className="flex justify-center">
              <AppIcon size={64} />
            </div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              {showRegister ? 'Create your account' : 'Sign in to your account'}
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              {showRegister 
                ? 'Join Metadata Builder to manage your database connections' 
                : 'Access your database connections and metadata tools'
              }
            </p>
          </div>

          <div className="bg-white py-8 px-6 shadow-lg rounded-lg">
            {showRegister ? (
              <form onSubmit={handleRegisterSubmit} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
                      First Name
                    </label>
                    <Input
                      id="first_name"
                      name="first_name"
                      type="text"
                      required
                      value={registerData.first_name}
                      onChange={handleRegisterInputChange}
                      placeholder="John"
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
                      Last Name
                    </label>
                    <Input
                      id="last_name"
                      name="last_name"
                      type="text"
                      required
                      value={registerData.last_name}
                      onChange={handleRegisterInputChange}
                      placeholder="Doe"
                      className="w-full"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="reg_username" className="block text-sm font-medium text-gray-700 mb-2">
                    Username
                  </label>
                  <Input
                    id="reg_username"
                    name="username"
                    type="text"
                    required
                    value={registerData.username}
                    onChange={handleRegisterInputChange}
                    placeholder="johndoe"
                    className="w-full"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={registerData.email}
                    onChange={handleRegisterInputChange}
                    placeholder="john@example.com"
                    className="w-full"
                  />
                </div>

                <div>
                  <label htmlFor="reg_password" className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <Input
                    id="reg_password"
                    name="password"
                    type="password"
                    required
                    value={registerData.password}
                    onChange={handleRegisterInputChange}
                    placeholder="Enter a secure password"
                    className="w-full"
                  />
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                    Confirm Password
                  </label>
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    value={registerData.confirmPassword}
                    onChange={handleRegisterInputChange}
                    placeholder="Confirm your password"
                    className="w-full"
                  />
                </div>

                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-green-600 hover:bg-green-700 text-white"
                >
                  {isLoading ? 'Creating account...' : 'Create account'}
                </Button>

                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setShowRegister(false)}
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    Already have an account? Sign in here
                  </button>
                </div>
              </form>
            ) : (
                            <form onSubmit={handleLoginSubmit} className="space-y-6">
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                    Username or Email
                  </label>
                  <Input
                    id="username"
                    name="username"
                    type="text"
                    required
                    value={formData.username}
                    onChange={handleLoginInputChange}
                    placeholder="Enter your username or email"
                    className="w-full"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleLoginInputChange}
                    placeholder="Enter your password"
                    className="w-full"
                  />
                </div>

                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </Button>

                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setShowRegister(true)}
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    Don't have an account? Register here
                  </button>
                </div>
              </form>
            )}
          </div>

          <div className="text-center">
            <div className="text-sm text-gray-500">
              <p className="font-medium">Default Admin Credentials:</p>
              <p>Username: <code className="bg-gray-100 px-1 rounded">admin</code></p>
              <p>Password: <code className="bg-gray-100 px-1 rounded">admin123</code></p>
              <p className="text-xs text-red-500 mt-1">⚠️ Change these in production!</p>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default LoginPage; 