import { request } from "./http";
import type {
  FundNavHistoryPeriod,
  FundNavHistoryResponse,
  FundRealtimeEstimateResponse,
  FundSnapshotResponse,
} from "./types";
import { buildQuery } from "./query";

export const getFundSnapshot = (code: string) => {
  return request<FundSnapshotResponse>(`/funds/${code}/snapshot`);
};

export const getFundNavHistory = (code: string, period: FundNavHistoryPeriod) => {
  const query = buildQuery({ period });
  return request<FundNavHistoryResponse>(`/funds/${code}/nav-history${query}`);
};

export const getFundRealtimeEstimate = (code: string) => {
  return request<FundRealtimeEstimateResponse>(`/funds/${code}/realtime-estimate`);
};
