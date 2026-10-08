/**
 * Shared Base Path Utility for Redis Workshops
 * 
 * Dynamically detects the workshop base path from the URL.
 * Works both when running standalone (localhost:8080) and when
 * proxied through the Workshop Hub (/workshop/{service-name}/).
 * 
 * This replaces the hardcoded path regex that was previously
 * duplicated in each workshop's basePath.js.
 */

/**
 * Get the base path for the current workshop.
 * 
 * Automatically detects if running under the Hub proxy by checking
 * for /workshop/{service-name} in the URL path.
 * 
 * @returns {string} The base path (e.g., '/workshop/session-management' or '/')
 */
export function getBasePath() {
  const defaultBase = process.env.BASE_URL || '/';
  const pathname = window.location.pathname || '';

  const proxyContext = getWorkshopProxyContext(pathname);

  if (proxyContext) {
    return proxyContext.basePath;
  }

  // Running standalone - return default base path without trailing slash
  return defaultBase.replace(/\/$/, '');
}

/**
 * Get the full API URL for a given endpoint.
 * 
 * Convenience function that combines the base path with an API endpoint.
 * Handles slash normalization automatically.
 * 
 * @param {string} endpoint - The API endpoint (e.g., '/api/session-info' or 'api/session-info')
 * @returns {string} The full API URL
 * 
 * @example
 * // When running at /workshop/session-management/
 * getApiUrl('/api/users') // => '/workshop/session-management/api/users'
 * getApiUrl('api/users')  // => '/workshop/session-management/api/users'
 * 
 * // When running standalone at /
 * getApiUrl('/api/users') // => '/api/users'
 */
export function getApiUrl(endpoint) {
  const basePath = getBasePath();
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  if (basePath === '' || basePath === '/') {
    return normalizedEndpoint;
  }
  
  return `${basePath}${normalizedEndpoint}`;
}

function getRuntimeLocation(location = globalThis.window?.location) {
  return location || { pathname: '', protocol: 'http:', hostname: 'localhost' };
}

function getWorkshopProxyContext(pathname = '') {
  const workshopMarker = '/workshop/';
  const workshopIndex = pathname.indexOf(workshopMarker);

  if (workshopIndex === -1) {
    return null;
  }

  const serviceName = pathname
    .slice(workshopIndex + workshopMarker.length)
    .split('/')[0];

  if (!serviceName) {
    return null;
  }

  const prefix = pathname.slice(0, workshopIndex).replace(/\/$/, '');
  const basePath = `${prefix}${workshopMarker}${serviceName}`;

  return {
    basePath,
    hubUrl: prefix ? `${prefix}/` : '/'
  };
}

function resolveRuntimeUrl({ location, port, getProxyUrl }) {
  const runtimeLocation = getRuntimeLocation(location);
  const proxyContext = getWorkshopProxyContext(runtimeLocation.pathname || '');

  if (proxyContext) {
    return getProxyUrl(proxyContext);
  }

  return `${runtimeLocation.protocol}//${runtimeLocation.hostname}:${port}/`;
}

/**
 * Resolve the Workshop Hub URL for the current runtime.
 *
 * When a workshop is running behind the hub proxy, this returns the hub root
 * path on the current origin. When a workshop is running standalone, it falls
 * back to the local hub port so workshop UIs do not need to hardcode `:9000`.
 *
 * @param {Object} [options]
 * @param {Location} [options.location] - Override location, mainly for tests
 * @param {number|string} [options.port=9000] - Local Workshop Hub port
 * @returns {string} The Workshop Hub URL for the current runtime
 */
export function getWorkshopHubUrl(options = {}) {
  return resolveRuntimeUrl({
    location: options.location,
    port: options.port || 9000,
    getProxyUrl: ({ hubUrl }) => hubUrl
  });
}

/**
 * Resolve the Redis Insight URL for the current runtime.
 *
 * Redis Insight must be accessed directly on its own port because it does not
 * work correctly behind the workshop proxy. This always resolves to the local
 * Redis Insight port on the current origin so workshop UIs do not need to
 * hardcode `:5540`.
 *
 * @param {Object} [options]
 * @param {Location} [options.location] - Override location, mainly for tests
 * @param {number|string} [options.port=5540] - Local Redis Insight port
 * @returns {string} The Redis Insight URL for the current runtime
 */
export function getRedisInsightUrl(options = {}) {
  const runtimeLocation = getRuntimeLocation(options.location);
  return `${runtimeLocation.protocol}//${runtimeLocation.hostname}:${options.port || 5540}/`;
}
