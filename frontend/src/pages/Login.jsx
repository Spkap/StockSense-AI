import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const { signInWithGoogle, loading, error } = useAuth();
  const navigate = useNavigate();
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleGoogleLogin = async () => {
    try {
      setIsLoggingIn(true);
      await signInWithGoogle();
      navigate('/dashboard'); // Redirect to dashboard after successful login
    } catch (error) {
      console.error('Login failed:', error);
      // Error is already handled in AuthContext
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">
            StockSense
          </h1>
          <p className="login-subtitle">
            AI-Powered Stock Analysis 
          </p>

          {error && (
            <div className="error-message">
              <span className="error-icon"></span>
              {error}
            </div>
          )}

          <button
            onClick={handleGoogleLogin}
            disabled={loading || isLoggingIn}
            className="google-login-button"
          >
            {isLoggingIn ? (
              <>
                <div className="spinner"></div>
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <img 
                  src="https://developers.google.com/identity/images/g-logo.png" 
                  alt="Google" 
                  className="google-icon"
                />
                <span>Continue with Google</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;

