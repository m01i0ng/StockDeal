import { apiClient } from "./http";

const TRACE_ID_STORAGE_KEY = "stockdeal-trace-id";

const generateTraceId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const getTraceId = () => {
  const cached = localStorage.getItem(TRACE_ID_STORAGE_KEY);
  if (cached) {
    return cached;
  }
  const traceId = generateTraceId();
  localStorage.setItem(TRACE_ID_STORAGE_KEY, traceId);
  return traceId;
};

export const setupApiInterceptors = () => {
  apiClient.interceptors.request.use((config) => {
    const headers = config.headers ?? {};
    if (typeof headers.set === "function") {
      headers.set("X-Trace-Id", getTraceId());
    } else {
      (headers as Record<string, string>)["X-Trace-Id"] = getTraceId();
    }

    return {
      ...config,
      headers,
    };
  });

  apiClient.interceptors.response.use((response) => response, (error) => {
    if (error?.response?.data && typeof error.response.data === "object") {
      const detail = (error.response.data as { detail?: string }).detail;
      if (detail) {
        error.message = detail;
      }
    }
    return Promise.reject(error);
  });
};
