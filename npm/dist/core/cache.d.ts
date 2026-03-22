export interface CacheOptions {
    ttlSeconds?: number;
}
export declare function setCache(key: string, value: any, options?: CacheOptions): Promise<void>;
export declare function getCache<T>(key: string): Promise<T | null>;
//# sourceMappingURL=cache.d.ts.map