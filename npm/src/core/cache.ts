/**
 * Redis / In-Memory Cache layer for Horizontal Scaling.
 * 
 * Uses in-memory Map by default (zero deps).
 * If REDIS_REST_URL and REDIS_REST_TOKEN are set (e.g. Upstash), 
 * it seamlessly switches to distributed Redis over HTTP.
 */
import axios from "axios";

export interface CacheOptions {
  ttlSeconds?: number;
}

const localCache = new Map<string, { value: any; expiry: number | null }>();

export async function setCache(key: string, value: any, options?: CacheOptions): Promise<void> {
  const redisUrl = process.env["REDIS_REST_URL"];
  const redisToken = process.env["REDIS_REST_TOKEN"];
  
  if (redisUrl && redisToken) {
    // Distributed Redis via REST
    try {
      let url = `${redisUrl}/set/${encodeURIComponent(key)}`;
      if (options?.ttlSeconds) {
        url += `/EX/${options.ttlSeconds}`;
      }
      await axios.post(url, typeof value === "string" ? value : JSON.stringify(value), {
        headers: { Authorization: `Bearer ${redisToken}` },
      });
      return;
    } catch (e) {
      console.warn("Redis error on set, falling back to local memory:", e);
    }
  }

  // Local Memory Fallback
  const expiry = options?.ttlSeconds ? Date.now() + options.ttlSeconds * 1000 : null;
  localCache.set(key, { value, expiry });
}

export async function getCache<T>(key: string): Promise<T | null> {
  const redisUrl = process.env["REDIS_REST_URL"];
  const redisToken = process.env["REDIS_REST_TOKEN"];

  if (redisUrl && redisToken) {
    try {
      const response = await axios.get(`${redisUrl}/get/${encodeURIComponent(key)}`, {
        headers: { Authorization: `Bearer ${redisToken}` },
      });
      if (response.data && response.data.result !== null) {
        try {
          return JSON.parse(response.data.result) as T;
        } catch {
          return response.data.result as T;
        }
      }
      return null;
    } catch (e) {
      console.warn("Redis error on get, falling back to local memory:", e);
    }
  }

  // Local Memory Fallback
  const record = localCache.get(key);
  if (!record) return null;
  if (record.expiry !== null && Date.now() > record.expiry) {
    localCache.delete(key);
    return null;
  }
  return record.value as T;
}
