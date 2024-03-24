
if (!import.meta.env.VITE_SERVER_URL) {
  alert('vite-error: the environment variable VITE_SERVER_URL is required during build!');
  throw new Error('VITE_SERVER_URL is required');
}

export const SERVER_URL = import.meta.env.VITE_SERVER_URL;
export const URL_BASE_NAME = import.meta.env.VITE_URL_BASE_NAME || '/';