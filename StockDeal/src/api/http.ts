import axios, { type AxiosRequestConfig, type AxiosError } from "axios";
import { showToast } from "vant";

export class ApiError extends Error {
  status: number;
  payload?: unknown;
  code?: string;

  constructor(message: string, status: number, payload?: unknown, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
    this.code = code;
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
  if (axios.isCancel(error) || error.code === "ERR_CANCELED") {
    return false;
  }
  if (error.code === "ECONNABORTED" || error.code === "ERR_NETWORK") {
    return true;
  }
  const status = error.response?.status ?? 0;
  return status >= 500 || status === 408 || status === 429;
};

const getErrorMessage = (payload: unknown, fallback: string) => {
  if (!payload) {
    return fallback;
  }
  if (typeof payload === "string") {
    return payload;
  }
  if (typeof payload === "object") {
    const maybeDetail = (payload as { detail?: string }).detail;
    if (maybeDetail) {
      return maybeDetail;
    }
    const maybeMessage = (payload as { message?: string }).message;
    if (maybeMessage) {
      return maybeMessage;
    }
  }
  return fallback;
};

export const normalizeApiError = (error: AxiosError) => {
  const status = error.response?.status ?? 0;
  const payload = error.response?.data;
  const message = getErrorMessage(payload, error.message);
  return new ApiError(message, status, payload, error.code);
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

export type RequestOptions = AxiosRequestConfig & {
  retries?: number;
  retryDelayMs?: number;
  retryOn?: (error: unknown, attempt: number) => boolean;
  toast?: boolean;
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
  options: RequestOptions = {}
): Promise<T> => {
  const { retries = 1, retryDelayMs = 300, retryOn, toast = true, ...rest } = options;
  let attempt = 0;

  while (true) {
    try {
      const response = await apiClient.request<T>({
        url: path,
        ...rest,
      });
      const method = (rest.method || "GET").toString().toUpperCase();
      if (toast && method !== "GET") {
        showToast("操作成功");
      }
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (axios.isCancel(error) || (axios.isAxiosError(error) && error.code === "ERR_CANCELED")) {
        throw error;
      }
      const shouldRetry = retryOn ? retryOn(error, attempt) : isRetryableError(error);
      if (attempt < retries && shouldRetry) {
        attempt += 1;
        await sleep(retryDelayMs * attempt);
        continue;
      }
      if (axios.isAxiosError(error)) {
        const normalizedError = normalizeApiError(error);
        if (toast) {
          showToast(normalizedError.message || "请求失败");
        }
        throw normalizedError;
      }
      if (toast) {
        showToast("请求失败");
      }
      throw error;
    }
  }
};
