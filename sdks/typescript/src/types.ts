/**
 * ASTRAEUS SDK Types
 *
 * Sprint 6: Multi-Language SDKs
 */

export interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  capabilities: string[];
  average_rating: number;
  total_calls: number;
  is_free: boolean;
  cost_per_request: number;
  endpoint: string;
  status: string;
}

export interface AgentListParams {
  category?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}

export interface AgentExecuteParams {
  agentId: string;
  inputData: Record<string, any>;
  waitForResult?: boolean;
}

export interface AgentCreateParams {
  name: string;
  description: string;
  endpoint: string;
  capabilities: string[];
  category?: string;
  is_free?: boolean;
  cost_per_request?: number;
}

export interface Contract {
  id: string;
  title: string;
  description: string;
  budget: number;
  status: string;
  created_at: string;
  awarded_to?: string;
}

export interface ContractCreateParams {
  title: string;
  description: string;
  budget: number;
  requirements?: Record<string, any>;
}

export interface ContractListParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export interface ContractListResponse {
  contracts: Contract[];
  total: number;
}

export interface PurchaseCreditsParams {
  amount: number;
  provider?: string;
}

export interface CreditBalance {
  balance: number;
  reserved: number;
  available: number;
}

export interface TransactionListParams {
  limit?: number;
  offset?: number;
}

export interface TransactionListResponse {
  transactions: any[];
  total: number;
}

export interface OrchestrationPlanParams {
  query: string;
  pattern?: string;
}

export interface MetricParams {
  metric_name: string;
  value: number;
  metric_type?: string;
  unit?: string;
  tags?: Record<string, any>;
}

export interface ReputationScore {
  agent_id: string;
  overall_reputation: number;
  trust_grade: string;
  quality_score: number;
  reliability_score: number;
  speed_score: number;
  honesty_score: number;
  collaboration_score: number;
  is_flagged: boolean;
}

export interface FraudAlertParams {
  fraud_type?: string;
  severity?: string;
}
