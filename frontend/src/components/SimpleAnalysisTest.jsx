import React from 'react';

const SimpleAnalysisTest = ({ onClose }) => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}>
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '8px',
        maxWidth: '500px',
        width: '90%'
      }}>
        <h2>Test Analysis Modal</h2>
        <p>This is a simple test to see if modals work.</p>
        <button onClick={onClose} style={{
          background: '#007bff',
          color: 'white',
          border: 'none',
          padding: '0.5rem 1rem',
          borderRadius: '4px',
          cursor: 'pointer'
        }}>
          Close Test
        </button>
      </div>
    </div>
  );
};

export default SimpleAnalysisTest;
