import React, { createContext, useContext, useEffect, useState } from 'react';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sign in with Google
  const signInWithGoogle = async () => {
    try {
      setError(null);
      setLoading(true);
      
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      
      // Store token in localStorage
      localStorage.setItem('firebase_token', idToken);
      
      // Send token to backend
      const backendResponse = await authAPI.login(idToken);
    
      
      console.log('Backend login successful:', backendResponse);
      
      // Set the user after successful backend verification
      setCurrentUser(result.user);
      console.log('Signed in user:', result.user);
      
      return result;
    } catch (error) {
      setError(error.message);
      console.error('Login error:', error);
      
      // Clean up on error
      localStorage.removeItem('firebase_token');
      setCurrentUser(null);
      
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Sign out
  const logout = async () => {
    try {
      setError(null);
      await signOut(auth);
      localStorage.removeItem('firebase_token');
      setCurrentUser(null);
    } catch (error) {
      setError(error.message);
      console.error('Logout error:', error);
      throw error;
    }
  };

  // Monitor auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      try {
        if (user) {
          // User is signed in
          const idToken = await user.getIdToken();
          localStorage.setItem('firebase_token', idToken);
          
          // Only set user if we have a valid token
          if (idToken) {
            setCurrentUser(user);
          }
        } else {
          // User is signed out
          localStorage.removeItem('firebase_token');
          setCurrentUser(null);
        }
      } catch (error) {
        console.error('Auth state change error:', error);
        setError(error.message);
        // On error, clear everything
        localStorage.removeItem('firebase_token');
        setCurrentUser(null);
      } finally {
        setLoading(false);
      }
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    signInWithGoogle,
    logout,
    loading,
    error,
    setError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
