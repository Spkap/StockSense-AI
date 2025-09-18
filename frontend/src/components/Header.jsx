import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Header = ({ title = "StockSense", subtitle = "Your Personal Stock Assistant" }) => {
  const { currentUser, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="dashboard-title">{title}</h1>
          <span className="dashboard-subtitle">{subtitle}</span>
        </div>
        
        <div className="header-right">
          <div className="user-info">
            <img 
              src={currentUser?.photoURL || 'https://via.placeholder.com/40'} 
              alt="Profile" 
              className="user-avatar"
            />
            <div className="user-details">
              <span className="user-name">{currentUser?.displayName || 'User'}</span>
            </div>
          </div>
          
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
