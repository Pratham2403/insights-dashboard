import { Dashboard } from '../types';

/**
 * Abstract interface for storage operations
 * This allows easy migration from localStorage to database
 */
interface StorageAdapter {
    getDashboards(): Promise<Dashboard[]>;
    saveDashboards(dashboards: Dashboard[]): Promise<void>;
    addDashboard(dashboard: Dashboard): Promise<void>;
    removeDashboard(dashboardId: string): Promise<void>;
    updateDashboard(dashboard: Dashboard): Promise<void>;
}

/**
 * localStorage implementation of StorageAdapter
 * Can be easily swapped with DatabaseStorageAdapter later
 */
class LocalStorageAdapter implements StorageAdapter {
    private readonly STORAGE_KEY = 'sprinklr_dashboards';

    async getDashboards(): Promise<Dashboard[]> {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (!stored) return [];

            const dashboards = JSON.parse(stored);
            // Convert date strings back to Date objects
            return dashboards.map((dashboard: any) => ({
                ...dashboard,
                createdAt: new Date(dashboard.createdAt),
                lastAccessed: new Date(dashboard.lastAccessed),
            }));
        } catch (error) {
            console.error('Error loading dashboards from localStorage:', error);
            return [];
        }
    }

    async saveDashboards(dashboards: Dashboard[]): Promise<void> {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(dashboards));
        } catch (error) {
            console.error('Error saving dashboards to localStorage:', error);
        }
    }

    async addDashboard(dashboard: Dashboard): Promise<void> {
        const dashboards = await this.getDashboards();
        const exists = dashboards.some((d) => d.id === dashboard.id);

        if (!exists) {
            dashboards.push(dashboard);
            await this.saveDashboards(dashboards);
        }
    }

    async removeDashboard(dashboardId: string): Promise<void> {
        const dashboards = await this.getDashboards();
        const filtered = dashboards.filter((d) => d.id !== dashboardId);
        await this.saveDashboards(filtered);
    }

    async updateDashboard(dashboard: Dashboard): Promise<void> {
        const dashboards = await this.getDashboards();
        const index = dashboards.findIndex((d) => d.id === dashboard.id);

        if (index !== -1) {
            dashboards[index] = dashboard;
            await this.saveDashboards(dashboards);
        }
    }
}

/**
 * Future database implementation placeholder
 * Can be implemented when migrating from localStorage
 */
class DatabaseStorageAdapter implements StorageAdapter {
    async getDashboards(): Promise<Dashboard[]> {
        // TODO: Implement API calls to backend database
        throw new Error('Database storage not implemented yet');
    }

    async saveDashboards(_dashboards: Dashboard[]): Promise<void> {
        // TODO: Implement API calls to backend database
        throw new Error('Database storage not implemented yet');
    }

    async addDashboard(_dashboard: Dashboard): Promise<void> {
        // TODO: Implement API calls to backend database
        throw new Error('Database storage not implemented yet');
    }

    async removeDashboard(_dashboardId: string): Promise<void> {
        // TODO: Implement API calls to backend database
        throw new Error('Database storage not implemented yet');
    }

    async updateDashboard(_dashboard: Dashboard): Promise<void> {
        // TODO: Implement API calls to backend database
        throw new Error('Database storage not implemented yet');
    }
}

/**
 * Main storage service that uses the configured adapter
 * This provides a consistent interface regardless of storage backend
 */
class DashboardStorageService {
    private adapter: StorageAdapter;

    constructor(adapter: StorageAdapter) {
        this.adapter = adapter;
    }

    // Dashboard CRUD operations
    async getAllDashboards(): Promise<Dashboard[]> {
        return this.adapter.getDashboards();
    }

    async addDashboard(dashboard: Dashboard): Promise<void> {
        return this.adapter.addDashboard(dashboard);
    }

    async removeDashboard(dashboardId: string): Promise<void> {
        return this.adapter.removeDashboard(dashboardId);
    }

    async updateDashboard(dashboard: Dashboard): Promise<void> {
        return this.adapter.updateDashboard(dashboard);
    }

    // Initialize dashboards from static data (one-time operation)
    async initializeFromStaticData(staticDashboards: any[]): Promise<void> {
        const existingDashboards = await this.getAllDashboards();

        // Only initialize if no dashboards exist
        if (existingDashboards.length === 0) {
            const dashboards = staticDashboards.map((dashboard) => ({
                ...dashboard,
                createdAt: new Date(dashboard.createdAt),
                lastAccessed: new Date(dashboard.lastAccessed),
            }));

            await this.adapter.saveDashboards(dashboards);
        }
    }

    // Migration utility for future use
    async migrateToNewAdapter(newAdapter: StorageAdapter): Promise<void> {
        const dashboards = await this.getAllDashboards();
        this.adapter = newAdapter;
        await this.adapter.saveDashboards(dashboards);
    }
}

// Create service instance with localStorage adapter
// To migrate to database later, just replace LocalStorageAdapter with DatabaseStorageAdapter
const dashboardStorage = new DashboardStorageService(new LocalStorageAdapter());

export {
    dashboardStorage,
    DashboardStorageService,
    LocalStorageAdapter,
    DatabaseStorageAdapter,
};
export type { StorageAdapter };
