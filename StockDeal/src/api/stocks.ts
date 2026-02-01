import { request } from "./http";
import type { StockRealtimeQuoteResponse } from "./types";

export const getStockRealtimeQuote = (code: string) => {
  return request<StockRealtimeQuoteResponse>(`/stocks/${code}/realtime`);
};
