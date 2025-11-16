/**
 * IndexedDB Cache for WolfTrace
 * Provides client-side caching for graph data and sessions
 */

const DB_NAME = 'WolfTraceDB';
const DB_VERSION = 1;
const STORES = {
  GRAPH: 'graph',
  SESSIONS: 'sessions',
  CACHE: 'cache'
};

class CacheManager {
  constructor() {
    this.db = null;
  }

  async init() {
    // Only run in browser environment
    if (typeof window === 'undefined' || typeof indexedDB === 'undefined') {
      return Promise.resolve(null);
    }
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores if they don't exist
        if (!db.objectStoreNames.contains(STORES.GRAPH)) {
          db.createObjectStore(STORES.GRAPH, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(STORES.SESSIONS)) {
          db.createObjectStore(STORES.SESSIONS, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(STORES.CACHE)) {
          const cacheStore = db.createObjectStore(STORES.CACHE, { keyPath: 'key' });
          cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  async saveGraph(graphData, id = 'current') {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.GRAPH], 'readwrite');
      const store = transaction.objectStore(STORES.GRAPH);
      
      const data = {
        id,
        data: graphData,
        timestamp: Date.now()
      };
      
      const request = store.put(data);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getGraph(id = 'current') {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.GRAPH], 'readonly');
      const store = transaction.objectStore(STORES.GRAPH);
      const request = store.get(id);
      
      request.onsuccess = () => {
        const result = request.result;
        resolve(result ? result.data : null);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async saveSession(sessionData) {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.SESSIONS], 'readwrite');
      const store = transaction.objectStore(STORES.SESSIONS);
      
      const data = {
        id: sessionData.id || `session_${Date.now()}`,
        ...sessionData,
        timestamp: Date.now()
      };
      
      const request = store.put(data);
      request.onsuccess = () => resolve(data.id);
      request.onerror = () => reject(request.error);
    });
  }

  async getSessions() {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.SESSIONS], 'readonly');
      const store = transaction.objectStore(STORES.SESSIONS);
      const request = store.getAll();
      
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  async cacheData(key, data, ttl = 3600000) {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.CACHE], 'readwrite');
      const store = transaction.objectStore(STORES.CACHE);
      
      const cacheItem = {
        key,
        data,
        timestamp: Date.now(),
        ttl
      };
      
      const request = store.put(cacheItem);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getCachedData(key) {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.CACHE], 'readonly');
      const store = transaction.objectStore(STORES.CACHE);
      const request = store.get(key);
      
      request.onsuccess = () => {
        const result = request.result;
        if (!result) {
          resolve(null);
          return;
        }
        
        // Check if expired
        const age = Date.now() - result.timestamp;
        if (age > result.ttl) {
          // Delete expired cache
          store.delete(key);
          resolve(null);
          return;
        }
        
        resolve(result.data);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async clearCache() {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([STORES.CACHE], 'readwrite');
      const store = transaction.objectStore(STORES.CACHE);
      const request = store.clear();
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

export const cacheManager = new CacheManager();

