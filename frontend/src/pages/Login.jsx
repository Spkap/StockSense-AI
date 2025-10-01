import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button';

const Login = () => {
  const { signInWithGoogle, loading } = useAuth();
  const navigate = useNavigate();
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleGoogleLogin = async () => {
    try {
      setIsLoggingIn(true);
      await signInWithGoogle();
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="hero bg-black min-h-screen">
      <div className="hero-content text-center">
        <div className="max-w-md">
          <h1 className="text-5xl font-bold text-white">StockSense</h1>
          <p className="py-6 text-white">
            AI-Powered Stock Analysis for Smarter Investments
          </p>

          <Button
            onClick={handleGoogleLogin}
            disabled={loading || isLoggingIn}
            className="btn bg-white text-black border-[#e5e5e5]"
          >
            <img
              src="https://www.svgrepo.com/show/355037/google.svg"
              alt="Google logo"
              className="w-5 h-5"
            />
            <span className='text-black'>Login With Google</span>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Login;

