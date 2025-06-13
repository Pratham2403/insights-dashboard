import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Dashboard } from '../types';

interface DashboardContextType {
    currentDashboard: Dashboard | null;
    dashboards: Dashboard[];
    setCurrentDashboard: (dashboard: Dashboard) => void;
    addDashboard: (dashboard: Dashboard) => void;
    removeDashboard: (dashboardId: string) => void;
}

const DashboardContext = createContext<DashboardContextType | undefined>(
    undefined
);

export const DashboardProvider: React.FC<{ children: ReactNode }> = ({
    children,
}) => {
    const [currentDashboard, setCurrentDashboard] = useState<Dashboard | null>(
        null
    );
    const [dashboards, setDashboards] = useState<Dashboard[]>([]);

    const addDashboard = (dashboard: Dashboard) => {
        setDashboards((prev) => {
            // Check if dashboard with same ID already exists
            const exists = prev.some((d) => d.id === dashboard.id);
            if (exists) {
                return prev; // Return unchanged array if duplicate found
            }
            return [...prev, dashboard];
        });
    };

    const removeDashboard = (dashboardId: string) => {
        setDashboards((prev) => prev.filter((d) => d.id !== dashboardId));
        if (currentDashboard?.id === dashboardId) {
            setCurrentDashboard(null);
        }
    };

    const value: DashboardContextType = {
        currentDashboard,
        dashboards,
        setCurrentDashboard,
        addDashboard,
        removeDashboard,
    };

    return (
        <DashboardContext.Provider value={value}>
            {children}
        </DashboardContext.Provider>
    );
};

export const useDashboardContext = () => {
    const context = useContext(DashboardContext);
    if (context === undefined) {
        throw new Error(
            'useDashboardContext must be used within a DashboardProvider'
        );
    }
    return context;
};
