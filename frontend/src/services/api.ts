export const API_ORIGIN = 'http://localhost:8000';
const BASE_URL = `${API_ORIGIN}/api`;

export type ApiParams = Record<string, string | number | boolean | null | undefined>;

export class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

const getError = async (res: Response) => {
    const errorData = await res.json().catch(() => ({})) as { detail?: string };
    return new ApiError(errorData.detail || 'Request failed', res.status);
};

export const api = {
    async get<T>(endpoint: string, params?: ApiParams): Promise<T> {
        let url = `${BASE_URL}${endpoint}`;
        if (params) {
            const query = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    query.append(key, String(value));
                }
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
        const res = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body)
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async put<T>(endpoint: string, body: unknown): Promise<T> {
        const res = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body)
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async upload<T>(endpoint: string, body: FormData): Promise<T> {
        const res = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            credentials: 'include',
            body,
        });

        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    },

    async delete<T = null>(endpoint: string): Promise<T | null> {
        const res = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });

        if (res.status === 204) return null;
        if (!res.ok) throw await getError(res);
        return res.json() as Promise<T>;
    }
}
