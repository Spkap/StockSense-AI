import React from "react";

const Button = ({ 
  children = "",   
  className = "",          
  onClick = () => {},      
  ...props            
}) => {
  return (
    <button 
      className={`btn ${className}`}
      onClick={onClick} 
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
