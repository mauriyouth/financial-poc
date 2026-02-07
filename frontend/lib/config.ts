export const getApiBaseUrl = () => {
    if (typeof window !== 'undefined') {
        const injectedUrl = (window as any).ENV?.NEXT_PUBLIC_API_URL;
        if (injectedUrl) return injectedUrl;
    }
    // Server-side: prefer internal API_URL, fallback to public URL or localhost
    return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export const getWsBaseUrl = () => {
    const apiBase = getApiBaseUrl();
    // Handle both http:// and https:// by replacing with ws:// and wss://
    return apiBase.replace(/^http/, 'ws');
};
