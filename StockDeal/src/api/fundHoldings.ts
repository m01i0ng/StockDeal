import { request } from "./http";
import type {
  FundConversionCreateRequest,
  FundConversionResponse,
  FundHoldingPositionResponse,
  FundHoldingTransactionCreateRequest,
  FundHoldingTransactionResponse,
} from "./types";
import { buildQuery } from "./query";

export const listFundHoldings = (accountId: number, fundCode?: string) => {
  const query = buildQuery({ account_id: accountId, fund_code: fundCode });
  return request<FundHoldingPositionResponse[]>(`/fund-holdings${query}`);
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
