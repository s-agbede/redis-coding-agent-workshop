/**
 * Base Path Utility for Workshop Template
 * 
 * Dynamically detects the workshop base path from the URL.
 * Works both when running standalone and when proxied through the Workshop Hub.
 */

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

/**
 * Get the base path for the current workshop.
 */
export function getBasePath() {
  const defaultBase = process.env.BASE_URL || '/';
  const pathname = window.location.pathname || '';

  if (pathname === '/guide' || pathname.startsWith('/guide/')) return '/guide';

  const proxyContext = getWorkshopProxyContext(pathname);

  if (proxyContext) {
    return proxyContext.basePath;
  }

  return defaultBase.replace(/\/$/, '');
}

/**
 * Get the full API URL for a given endpoint.
 */
export function getApiUrl(endpoint) {
  const basePath = getBasePath();
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  if (basePath === '' || basePath === '/' || basePath === '/guide') {
    return normalizedEndpoint;
  }
  
  return `${basePath}${normalizedEndpoint}`;
}

/**
 * Resolve the Workshop Hub URL for the current runtime.
 */
export function getWorkshopHubUrl(options = {}) {
  const location = options.location || window.location;
  const port = options.port || 9000;
  const proxyContext = getWorkshopProxyContext(location.pathname || '');

  if (proxyContext) {
    return proxyContext.hubUrl;
  }

  return `${location.protocol}//${location.hostname}:${port}/`;
}

/**
 * Resolve the Redis Insight URL for the current runtime.
 */
export function getRedisInsightUrl(options = {}) {
  const location = options.location || window.location;
  const port = options.port || 5540;
  const proxyContext = getWorkshopProxyContext(location.pathname || '');

  if (proxyContext) {
    return `${proxyContext.hubUrl}redis-insight/`;
  }

  return `${location.protocol}//${location.hostname}:${port}/`;
}
