import axios, { type AxiosRequestConfig } from "axios";

export class ApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
  timeout: 8000,
  headers: {
    "Content-Type": "application/json",
  },
});

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const isRetryableError = (error: unknown) => {
  if (!axios.isAxiosError(error)) {
    return false;
  }
  if (error.code === "ECONNABORTED" || error.code === "ERR_NETWORK") {
    return true;
  }
  const status = error.response?.status ?? 0;
  return status >= 500 || status === 408 || status === 429;
};

export const withTimeout = (timeoutMs: number) => {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  return {
    signal: controller.signal,
    cancel: () => controller.abort(),
    clear: () => window.clearTimeout(timer),
  };
};

export const createRequestCanceler = () => {
  const controller = new AbortController();
  return {
    signal: controller.signal,
    cancel: () => controller.abort(),
  };
};

export const createLatestRequestController = () => {
  let controller: AbortController | null = null;

  return () => {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();
    return controller;
  };
};

export const request = async <T>(
  path: string,
  options: AxiosRequestConfig & { retries?: number; retryDelayMs?: number } = {}
): Promise<T> => {
  const { retries = 1, retryDelayMs = 300, ...rest } = options;
  let attempt = 0;

  while (true) {
    try {
      const response = await apiClient.request<T>({
        url: path,
        ...rest,
      });
      return response.data;
    } catch (error) {
      if (attempt < retries && isRetryableError(error)) {
        attempt += 1;
        await sleep(retryDelayMs * attempt);
        continue;
      }
      if (axios.isAxiosError(error)) {
        const status = error.response?.status ?? 0;
        const payload = error.response?.data;
        const message =
          typeof payload === "string"
            ? payload
            : (payload as { detail?: string })?.detail ?? error.message;
        throw new ApiError(message, status, payload);
      }
      throw error;
    }
  }
};
