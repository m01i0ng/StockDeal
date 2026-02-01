export type FundNavHistoryPeriod =
  | "one_week"
  | "one_month"
  | "three_months"
  | "one_year"
  | "since_inception";

export interface BasicInfoItem {
  item: string;
  value: string | null;
}

export interface FundNav {
  date: string;
  nav: number | string;
  nav_7d?: number | string | null;
}

export interface FundHolding {
  quarter: string;
  stock_code: string;
  stock_name: string;
  weight_percent?: string | null;
  market_value?: string | null;
}

export interface FundNavHistoryItem {
  date: string;
  nav: number | string;
  daily_growth?: number | string | null;
  nav_7d?: number | string | null;
}

export interface FundNavHistoryResponse {
  code: string;
  name?: string | null;
  type?: string | null;
  period: FundNavHistoryPeriod;
  data: FundNavHistoryItem[];
}

export interface FundSnapshotResponse {
  code: string;
  name?: string | null;
  type?: string | null;
  basic_info: BasicInfoItem[];
  nav: FundNav;
  holdings: FundHolding[];
}

export interface FundHoldingEstimate {
  stock_code: string;
  stock_name: string;
  weight_percent?: string | null;
  change_percent?: number | null;
  contribution_percent?: number | null;
}

export interface FundRealtimeEstimateResponse {
  code: string;
  name?: string | null;
  type?: string | null;
  nav: FundNav;
  estimated_nav?: number | null;
  estimated_growth_percent?: number | null;
  holdings: FundHoldingEstimate[];
  skipped: string[];
}

export type StockMarket = "A" | "H";

export interface StockRealtimeQuoteResponse {
  code: string;
  market: StockMarket;
  latest_price?: number | null;
  change_percent?: number | null;
}

export interface FundAccountCreateRequest {
  name: string;
  remark?: string | null;
  default_buy_fee_percent?: number;
}

export interface FundAccountUpdateRequest {
  name?: string | null;
  remark?: string | null;
  default_buy_fee_percent?: number | null;
}

export interface FundAccountResponse {
  id: number;
  name: string;
  remark?: string | null;
  default_buy_fee_percent: number;
  created_at: string;
}

export interface FundHoldingPositionResponse {
  holding_id: number;
  account_id: number;
  fund_code: string;
  total_amount: number;
  total_shares: number;
  estimated_nav?: number | null;
  estimated_value?: number | null;
  estimated_profit?: number | null;
  estimated_profit_percent?: number | null;
  updated_at: string;
}

export interface FundAccountDetailResponse extends FundAccountResponse {
  holdings: FundHoldingPositionResponse[];
  total_cost: number;
  total_value?: number | null;
  total_profit?: number | null;
  total_profit_percent?: number | null;
}

export interface FundAccountSummaryResponse {
  account_id: number;
  total_cost: number;
  total_value?: number | null;
  total_profit?: number | null;
  total_profit_percent?: number | null;
}

export type FundTradeType = "buy" | "sell";

export type FundTradeStatus = "pending" | "confirmed" | "cancelled";

export interface FundHoldingTransactionCreateRequest {
  account_id: number;
  fund_code: string;
  trade_type: FundTradeType;
  amount: number;
  fee_percent?: number | null;
  trade_date: string;
  is_after_cutoff?: boolean;
  remark?: string | null;
}

export interface FundHoldingCreateRequest {
  account_id: number;
  fund_code: string;
  total_amount: number;
  profit_amount: number;
  remark?: string | null;
}

export interface FundHoldingUpdateRequest {
  total_amount: number;
  total_shares: number;
}

export interface FundHoldingTransactionResponse {
  id: number;
  account_id: number;
  holding_id?: number | null;
  conversion_id?: number | null;
  fund_code: string;
  trade_type: FundTradeType;
  status: FundTradeStatus;
  amount: number;
  fee_percent: number;
  fee_amount: number;
  confirmed_nav: number;
  confirmed_nav_date: string;
  shares: number;
  holding_amount?: number | null;
  profit_amount?: number | null;
  trade_time: string;
  remark?: string | null;
}

export interface FundConversionCreateRequest {
  account_id: number;
  from_fund_code: string;
  to_fund_code: string;
  from_amount: number;
  from_fee_percent?: number | null;
  to_amount: number;
  to_fee_percent?: number | null;
  trade_date: string;
  is_after_cutoff?: boolean;
  remark?: string | null;
}

export interface FundConversionResponse {
  id: number;
  account_id: number;
  from_fund_code: string;
  to_fund_code: string;
  trade_time: string;
  remark?: string | null;
  created_at: string;
  from_transaction: FundHoldingTransactionResponse;
  to_transaction: FundHoldingTransactionResponse;
}
