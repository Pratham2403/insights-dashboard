import React, { useState, useEffect, useRef } from 'react';
import { Plus, BarChart3, X, Trash2 } from 'lucide-react';
import { useDashboardContext } from '../context/DashboardContext';
import { useChatContext } from '../context/ChatContext';
import { Dashboard } from '../types';
import { v4 as uuidv4 } from 'uuid';
import dashboardsData from '../data/dashboards.json';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
    const {
        currentDashboard,
        dashboards,
        setCurrentDashboard,
        addDashboard,
        removeDashboard,
    } = useDashboardContext();
    const { clearMessages } = useChatContext();
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newDashboardName, setNewDashboardName] = useState('');
    const initializeRef = useRef(false);

    useEffect(() => {
        // Initialize dashboards from JSON on first load only
        if (!initializeRef.current) {
            dashboardsData.forEach((dashboard) => {
                addDashboard({
                    ...dashboard,
                    createdAt: new Date(dashboard.createdAt),
                    lastAccessed: new Date(dashboard.lastAccessed),
                });
            });
            initializeRef.current = true;
        }
    }, [addDashboard]);

    const handleDashboardSelect = (dashboard: Dashboard) => {
        if (currentDashboard?.id !== dashboard.id) {
            clearMessages(); // Clear chat when switching dashboards
            setCurrentDashboard({
                ...dashboard,
                lastAccessed: new Date(),
            });
        }
        onClose();
    };

    const handleCreateDashboard = () => {
        if (newDashboardName.trim()) {
            const newDashboard: Dashboard = {
                id: uuidv4(),
                name: newDashboardName.trim(),
                type: 'custom',
                description: 'Custom dashboard created by user',
                icon: 'BarChart3',
                color: 'purple',
                dataFile: 'brandHealthData.json', // Default to brand health data
                createdAt: new Date(),
                lastAccessed: new Date(),
            };

            addDashboard(newDashboard);
            setNewDashboardName('');
            setShowCreateForm(false);
            handleDashboardSelect(newDashboard);
        }
    };

    const handleDeleteDashboard = (
        e: React.MouseEvent,
        dashboardId: string
    ) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this dashboard?')) {
            removeDashboard(dashboardId);
        }
    };

    return (
        <>
            {/* Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-40"
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <div
                className={`fixed left-0 top-0 h-full w-80 bg-white shadow-xl z-50 transform transition-transform duration-300 flex flex-col ${
                    isOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                {/* Header - Fixed */}
                <div className="flex-shrink-0 p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold text-gray-900">
                            Dashboards
                        </h2>
                        <button
                            onClick={onClose}
                            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                        Manage your analytics dashboards
                    </p>
                </div>

                {/* Dashboard List - Scrollable */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
                    {dashboards.map((dashboard) => {
                        const isActive = currentDashboard?.id === dashboard.id;

                        return (
                            <div
                                key={dashboard.id}
                                className={`group relative p-4 rounded-xl border cursor-pointer transition-all duration-200 hover:shadow-md ${
                                    isActive
                                        ? 'border-purple-300 bg-purple-50 shadow-sm'
                                        : 'border-gray-200 bg-white hover:bg-gray-50'
                                }`}
                                onClick={() => handleDashboardSelect(dashboard)}
                            >
                                <div className="flex items-start space-x-3">
                                    <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 text-white flex-shrink-0">
                                        <BarChart3 className="w-5 h-5" />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <h3
                                            className={`font-medium truncate ${
                                                isActive
                                                    ? 'text-purple-900'
                                                    : 'text-gray-900'
                                            }`}
                                        >
                                            {dashboard.name}
                                        </h3>
                                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                                            {dashboard.description}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-2">
                                            Last accessed:{' '}
                                            {dashboard.lastAccessed.toLocaleDateString()}
                                        </p>
                                    </div>

                                    {/* Delete button */}
                                    {dashboard.type === 'custom' && (
                                        <button
                                            onClick={(e) =>
                                                handleDeleteDashboard(
                                                    e,
                                                    dashboard.id
                                                )
                                            }
                                            className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all duration-200 flex-shrink-0"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Create New Dashboard - Fixed at bottom */}
                <div className="flex-shrink-0 p-4 border-t border-gray-200 bg-gray-50">
                    {showCreateForm ? (
                        <div className="space-y-3">
                            <input
                                type="text"
                                value={newDashboardName}
                                onChange={(e) =>
                                    setNewDashboardName(e.target.value)
                                }
                                placeholder="Dashboard name..."
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
                                autoFocus
                            />
                            <div className="flex space-x-2">
                                <button
                                    onClick={handleCreateDashboard}
                                    disabled={!newDashboardName.trim()}
                                    className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-all duration-200 text-sm font-medium"
                                >
                                    Create
                                </button>
                                <button
                                    onClick={() => {
                                        setShowCreateForm(false);
                                        setNewDashboardName('');
                                    }}
                                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors text-sm"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button
                            onClick={() => setShowCreateForm(true)}
                            className="w-full flex items-center justify-center space-x-2 p-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-purple-400 hover:text-purple-600 transition-all duration-200"
                        >
                            <Plus className="w-5 h-5" />
                            <span className="font-medium">
                                Create New Dashboard
                            </span>
                        </button>
                    )}
                </div>
            </div>
        </>
    );
};

export default Sidebar;
