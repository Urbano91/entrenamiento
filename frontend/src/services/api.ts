const configuredApiOrigin = import.meta.env.VITE_API_ORIGIN?.trim() || '';

// During local development, requests stay on the Vite origin and its proxy
// forwards them to VITE_API_ORIGIN. This keeps session cookies first-party
// when the frontend is opened from another device on the local network.
export const API_ORIGIN = import.meta.env.DEV
    ? ''
    : configuredApiOrigin.replace(/\/+$/, '');

const withLeadingSlash = (path: string) => path.startsWith('/') ? path : `/${path}`;

export const fastApiResourceUrl = (path: string) => (
    `${API_ORIGIN}${withLeadingSlash(path)}`
);

export const apiEndpointUrl = (endpoint: string) => (
    fastApiResourceUrl(`/api${withLeadingSlash(endpoint)}`)
);

export const exerciseCoverUrl = (exerciseId: number) => (
    apiEndpointUrl(`/ejercicios/${exerciseId}/portada`)
);

export const exerciseAnimationUrl = (exerciseId: number) => (
    apiEndpointUrl(`/ejercicios/${exerciseId}/animacion`)
);

export const imageUrl = (imageId: number) => apiEndpointUrl(`/imagenes/${imageId}`);

type ApiParamScalar = string | number | boolean;
export type ApiParams = Record<
    string,
    ApiParamScalar | readonly ApiParamScalar[] | null | undefined
>;

export class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

const readableDetail = (detail: unknown): string => {
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map(item => {
            if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
                return item.msg;
            }
            return '';
        }).filter(Boolean).join(' ');
    }
    return '';
};

const getError = async (res: Response) => {
    const rawBody = await res.text().catch(() => '');
    let detail = '';
    if (rawBody) {
        try {
            detail = readableDetail((JSON.parse(rawBody) as { detail?: unknown }).detail);
        } catch {
            detail = '';
        }
    }
    const fallback = res.status >= 500
        ? 'Ha ocurrido un error inesperado en el servidor.'
        : `La solicitud fue rechazada (HTTP ${res.status}).`;
    return new ApiError(detail || fallback, res.status);
};

export const api = {
    async get<T>(endpoint: string, params?: ApiParams): Promise<T> {
        let url = apiEndpointUrl(endpoint);
        if (params) {
            const query = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value === undefined || value === null || value === '') return;
                const values = Array.isArray(value) ? value : [value];
                values.forEach(item => query.append(key, String(item)));
            });
            const qs = query.toString();
            if (qs) url += `?${qs}`;
        }

        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async post<T>(endpoint: string, body: unknown): Promise<T> {
        const res = await fetch(apiEndpointUrl(endpoint), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body)
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async put<T>(endpoint: string, body: unknown): Promise<T> {
        const res = await fetch(apiEndpointUrl(endpoint), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body)
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async upload<T>(endpoint: string, body: FormData): Promise<T> {
        const res = await fetch(apiEndpointUrl(endpoint), {
            method: 'POST',
            credentials: 'include',
            body,
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async delete<T = null>(endpoint: string): Promise<T | null> {
        const res = await fetch(apiEndpointUrl(endpoint), {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });

        if (res.status === 204) return null;
        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async download(endpoint: string, params?: ApiParams): Promise<{ blob: Blob; filename: string }> {
        let url = apiEndpointUrl(endpoint);
        if (params) {
            const query = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value === undefined || value === null || value === '') return;
                const values = Array.isArray(value) ? value : [value];
                values.forEach(item => query.append(key, String(item)));
            });
            const qs = query.toString();
            if (qs) url += `?${qs}`;
        }
        const res = await fetch(url, { credentials: 'include' });
        if (!res.ok) throw await getError(res);
        const disposition = res.headers.get('Content-Disposition') || '';
        const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
        const fallback = disposition.match(/filename="?([^";]+)"?/i)?.[1];
        return {
            blob: await res.blob(),
            filename: encoded ? decodeURIComponent(encoded) : fallback || 'exportacion.xlsx',
        };
    }
}
