import { request } from "./http";
import type {
  FundAccountCreateRequest,
  FundAccountDetailResponse,
  FundAccountResponse,
  FundAccountSummaryResponse,
  FundAccountUpdateRequest,
} from "./types";

export const listFundAccounts = () => {
  return request<FundAccountResponse[]>("/fund-accounts");
};

export const createFundAccount = (payload: FundAccountCreateRequest) => {
  return request<FundAccountResponse>("/fund-accounts", {
    method: "POST",
    data: payload,
  });
};

export const updateFundAccount = (accountId: number, payload: FundAccountUpdateRequest) => {
  return request<FundAccountResponse>(`/fund-accounts/${accountId}`, {
    method: "PUT",
    data: payload,
  });
};

export const getFundAccountDetail = (accountId: number) => {
  return request<FundAccountDetailResponse>(`/fund-accounts/${accountId}`);
};

export const getFundAccountSummary = (accountId: number) => {
  return request<FundAccountSummaryResponse>(`/fund-accounts/${accountId}/summary`);
};
