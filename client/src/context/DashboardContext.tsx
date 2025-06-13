import React, {
    createContext,
    useContext,
    useState,
    ReactNode,
    useEffect,
} from 'react';
import { Dashboard } from '../types';
import { dashboardStorage } from '../services/storageService';

interface DashboardContextType {
    currentDashboard: Dashboard | null;
    dashboards: Dashboard[];
    setCurrentDashboard: (dashboard: Dashboard) => void;
    addDashboard: (dashboard: Dashboard) => void;
    removeDashboard: (dashboardId: string) => void;
    isLoading: boolean;
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
    const [isLoading, setIsLoading] = useState(true);

    // Load dashboards from storage on mount
    useEffect(() => {
        const loadDashboards = async () => {
            try {
                setIsLoading(true);
                const storedDashboards =
                    await dashboardStorage.getAllDashboards();
                setDashboards(storedDashboards);
            } catch (error) {
                console.error('Error loading dashboards:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadDashboards();
    }, []);

    const addDashboard = async (dashboard: Dashboard) => {
        try {
            await dashboardStorage.addDashboard(dashboard);
            setDashboards((prev) => {
                // Check if dashboard with same ID already exists
                const exists = prev.some((d) => d.id === dashboard.id);
                if (exists) {
                    return prev; // Return unchanged array if duplicate found
                }
                return [...prev, dashboard];
            });
        } catch (error) {
            console.error('Error adding dashboard:', error);
        }
    };

    const removeDashboard = async (dashboardId: string) => {
        try {
            await dashboardStorage.removeDashboard(dashboardId);
            setDashboards((prev) => prev.filter((d) => d.id !== dashboardId));
            if (currentDashboard?.id === dashboardId) {
                setCurrentDashboard(null);
            }
        } catch (error) {
            console.error('Error removing dashboard:', error);
        }
    };

    const handleSetCurrentDashboard = async (dashboard: Dashboard) => {
        try {
            // Update lastAccessed timestamp
            const updatedDashboard = {
                ...dashboard,
                lastAccessed: new Date(),
            };

            await dashboardStorage.updateDashboard(updatedDashboard);
            setCurrentDashboard(updatedDashboard);

            // Update the dashboard in the list as well
            setDashboards((prev) =>
                prev.map((d) => (d.id === dashboard.id ? updatedDashboard : d))
            );
        } catch (error) {
            console.error('Error updating dashboard:', error);
            setCurrentDashboard(dashboard); // Fallback to setting without persistence
        }
    };

    const value: DashboardContextType = {
        currentDashboard,
        dashboards,
        setCurrentDashboard: handleSetCurrentDashboard,
        addDashboard,
        removeDashboard,
        isLoading,
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
