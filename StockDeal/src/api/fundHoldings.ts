import { request } from "./http";
import type {
  FundConversionCreateRequest,
  FundConversionResponse,
  FundHoldingCreateRequest,
  FundHoldingPositionResponse,
  FundHoldingTransactionCreateRequest,
  FundHoldingTransactionResponse,
  FundHoldingUpdateRequest,
} from "./types";
import { buildQuery } from "./query";

export const listFundHoldings = (accountId: number, fundCode?: string) => {
  const query = buildQuery({ account_id: accountId, fund_code: fundCode });
  return request<FundHoldingPositionResponse[]>(`/fund-holdings${query}`);
};

export const createFundHolding = (payload: FundHoldingCreateRequest) => {
  return request<FundHoldingTransactionResponse>("/fund-holdings", {
    method: "POST",
    data: payload,
  });
};

export const getFundHoldingDetail = (holdingId: number) => {
  return request<FundHoldingPositionResponse>(`/fund-holdings/${holdingId}`);
};

export const updateFundHolding = (
  holdingId: number,
  payload: FundHoldingUpdateRequest
) => {
  return request<FundHoldingPositionResponse>(`/fund-holdings/${holdingId}`, {
    method: "PUT",
    data: payload,
  });
};

export const deleteFundHolding = (holdingId: number) => {
  return request<{ success: boolean }>(`/fund-holdings/${holdingId}`, {
    method: "DELETE",
  });
};

export const createFundTransaction = (payload: FundHoldingTransactionCreateRequest) => {
  return request<FundHoldingTransactionResponse>("/fund-holdings/transactions", {
    method: "POST",
    data: payload,
  });
};

export const listFundTransactions = (accountId: number, fundCode?: string) => {
  const query = buildQuery({ account_id: accountId, fund_code: fundCode });
  return request<FundHoldingTransactionResponse[]>(`/fund-holdings/transactions${query}`);
};

export const createFundConversion = (payload: FundConversionCreateRequest) => {
  return request<FundConversionResponse>("/fund-holdings/conversions", {
    method: "POST",
    data: payload,
  });
};

export const listFundConversions = (accountId: number) => {
  const query = buildQuery({ account_id: accountId });
  return request<FundConversionResponse[]>(`/fund-holdings/conversions${query}`);
};
