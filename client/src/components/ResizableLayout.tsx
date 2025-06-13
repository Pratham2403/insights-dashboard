import React, { useState, useRef, useCallback, useEffect } from 'react';
import { GripVertical } from 'lucide-react';

interface ResizableLayoutProps {
    leftPanel: React.ReactNode;
    rightPanel: React.ReactNode;
    minLeftWidth?: number;
    minRightWidth?: number;
    defaultLeftWidth?: number;
}

const ResizableLayout: React.FC<ResizableLayoutProps> = ({
    leftPanel,
    rightPanel,
    minLeftWidth = 300,
    minRightWidth = 300,
    defaultLeftWidth = 50, // percentage
}) => {
    const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const startXRef = useRef(0);
    const startWidthRef = useRef(0);

    const handleMouseDown = useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            setIsDragging(true);
            startXRef.current = e.clientX;
            startWidthRef.current = leftWidth;

            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        },
        [leftWidth]
    );

    const handleMouseMove = useCallback(
        (e: MouseEvent) => {
            if (!isDragging || !containerRef.current) return;

            const containerRect = containerRef.current.getBoundingClientRect();
            const containerWidth = containerRect.width;
            const deltaX = e.clientX - startXRef.current;
            const deltaPercentage = (deltaX / containerWidth) * 100;

            let newLeftWidth = startWidthRef.current + deltaPercentage;

            // Calculate minimum widths as percentages
            const minLeftPercentage = (minLeftWidth / containerWidth) * 100;
            const minRightPercentage = (minRightWidth / containerWidth) * 100;

            // Constrain the width
            newLeftWidth = Math.max(
                minLeftPercentage,
                Math.min(100 - minRightPercentage, newLeftWidth)
            );

            setLeftWidth(newLeftWidth);
        },
        [isDragging, minLeftWidth, minRightWidth]
    );

    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    }, []);

    useEffect(() => {
        if (isDragging) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);

            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isDragging, handleMouseMove, handleMouseUp]);

    return (
        <div ref={containerRef} className="flex h-full w-full">
            {/* Left Panel */}
            <div
                style={{ width: `${leftWidth}%` }}
                className="flex-shrink-0 overflow-hidden"
            >
                {leftPanel}
            </div>

            {/* Resizable Divider */}
            <div
                className={`relative flex items-center justify-center w-1 bg-gray-200 hover:bg-gray-300 cursor-col-resize transition-all duration-200 group ${
                    isDragging ? 'bg-purple-400 w-2' : ''
                }`}
                onMouseDown={handleMouseDown}
            >
                {/* Drag Handle */}
                <div
                    className={`absolute inset-y-0 flex items-center justify-center w-4 -ml-2 transition-all duration-200 ${
                        isDragging
                            ? 'bg-purple-100 border border-purple-300'
                            : 'group-hover:bg-gray-100'
                    } rounded-sm`}
                >
                    <GripVertical
                        className={`w-3 h-3 transition-colors duration-200 ${
                            isDragging
                                ? 'text-purple-600'
                                : 'text-gray-400 group-hover:text-gray-600'
                        }`}
                    />
                </div>

                {/* Visual feedback line */}
                <div
                    className={`absolute inset-y-0 w-0.5 transition-all duration-200 ${
                        isDragging ? 'bg-purple-500' : 'bg-transparent'
                    }`}
                />
            </div>

            {/* Right Panel */}
            <div
                style={{ width: `${100 - leftWidth}%` }}
                className="flex-shrink-0 overflow-hidden"
            >
                {rightPanel}
            </div>
        </div>
    );
};

export default ResizableLayout;
