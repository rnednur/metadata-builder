import React from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../AppIcon';

const Breadcrumb = ({ items = [] }) => {
  const navigate = useNavigate();

  const handleNavigation = (path) => {
    if (path) {
      navigate(path);
    }
  };

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const isClickable = item.path && !isLast;

          return (
            <li key={index} className="flex items-center space-x-2">
              {index > 0 && (
                <Icon 
                  name="ChevronRight" 
                  size={14} 
                  className="text-text-muted flex-shrink-0"
                />
              )}
              
              {isClickable ? (
                <button
                  onClick={() => handleNavigation(item.path)}
                  className="text-accent hover:text-accent-600 transition-colors duration-150 truncate max-w-32 sm:max-w-none"
                  title={item.label}
                >
                  {item.label}
                </button>
              ) : (
                <span 
                  className={`truncate max-w-32 sm:max-w-none ${
                    isLast ? 'text-text-primary font-medium' : 'text-text-muted'
                  }`}
                  title={item.label}
                >
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumb;