import React from 'react';
import * as LucideIcons from 'lucide-react';
import { HelpCircle, Database } from 'lucide-react';

function Icon({
    name,
    size = 24,
    color = "currentColor",
    className = "",
    strokeWidth = 2,
    ...props
}) {
    const IconComponent = LucideIcons[name];

    if (!IconComponent) {
        return <HelpCircle size={size} color="gray" strokeWidth={strokeWidth} className={className} {...props} />;
    }

    return <IconComponent
        size={size}
        color={color}
        strokeWidth={strokeWidth}
        className={className}
        {...props}
    />;
}

// App-specific icon component for the application logo
export const AppIcon = ({ size = 32, className = "", ...props }) => {
    return (
        <div className={`inline-flex items-center justify-center ${className}`} {...props}>
            <Database 
                size={size} 
                className="text-blue-600" 
                strokeWidth={2}
            />
        </div>
    );
};

export default Icon;