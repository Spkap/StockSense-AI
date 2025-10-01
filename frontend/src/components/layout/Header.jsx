import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../ui/Button';

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
    <div className="navbar bg-blaxk shadow-md border-b border-white px-4 py-2 flex justify-between items-center">
      {/* Left Section - Title */}
      <div className="flex-1">
        <div className="flex flex-col">
          <span className="text-lg font-bold text-white">{title}</span>
          <span className="text-sm text-gray-500">{subtitle}</span>
        </div>
      </div>

      <div className="flex-none gap-2">
        <div className="flex flex-col items-end">
        </div>

      <Button
       className="btn btn-error"
        onClick={handleLogout}
      >
        <span className="text-white">Logout</span>
      </Button>

      </div>
    </div>
  );
};

export default Header;

