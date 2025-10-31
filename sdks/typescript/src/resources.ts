/**
 * ASTRAEUS SDK Resources
 *
 * API resource classes for agents, contracts, payments, etc.
 *
 * Sprint 6: Multi-Language SDKs
 */

import { AxiosInstance } from 'axios';
import type * as Types from './types';

class BaseResource {
  constructor(protected axios: AxiosInstance) {}
}

export class AgentsResource extends BaseResource {
  async list(params?: Types.AgentListParams): Promise<Types.AgentListResponse> {
    const response = await this.axios.get('/api/v1/marketplace', { params });
    return response.data;
  }

  async get(agentId: string): Promise<Types.Agent> {
    const response = await this.axios.get(`/api/v1/marketplace/${agentId}`);
    return response.data;
  }

  async execute(params: Types.AgentExecuteParams): Promise<any> {
    const response = await this.axios.post('/api/v1/agents/execute', params);
    return response.data;
  }

  async create(params: Types.AgentCreateParams): Promise<Types.Agent> {
    const response = await this.axios.post('/api/v1/agents', params);
    return response.data;
  }
}

export class ContractsResource extends BaseResource {
  async create(params: Types.ContractCreateParams): Promise<Types.Contract> {
    const response = await this.axios.post('/api/v1/contracts', params);
    return response.data;
  }

  async get(contractId: string): Promise<Types.Contract> {
    const response = await this.axios.get(`/api/v1/contracts/${contractId}`);
    return response.data;
  }

  async list(params?: Types.ContractListParams): Promise<Types.ContractListResponse> {
    const response = await this.axios.get('/api/v1/contracts', { params });
    return response.data;
  }

  async award(contractId: string, agentId: string): Promise<any> {
    const response = await this.axios.post(`/api/v1/contracts/${contractId}/award`, {
      agent_id: agentId
    });
    return response.data;
  }
}

export class PaymentsResource extends BaseResource {
  async purchaseCredits(params: Types.PurchaseCreditsParams): Promise<any> {
    const response = await this.axios.post('/api/v1/payments/credits/purchase', params);
    return response.data;
  }

  async getBalance(): Promise<Types.CreditBalance> {
    const response = await this.axios.get('/api/v1/payments/credits/balance');
    return response.data;
  }

  async getTransactions(params?: Types.TransactionListParams): Promise<Types.TransactionListResponse> {
    const response = await this.axios.get('/api/v1/payments/credits/transactions', { params });
    return response.data;
  }
}

export class OrchestrationResource extends BaseResource {
  async createPlan(params: Types.OrchestrationPlanParams): Promise<any> {
    const response = await this.axios.post('/api/v1/orchestration/plan', params);
    return response.data;
  }

  async executePlan(planId: string): Promise<any> {
    const response = await this.axios.post(`/api/v1/orchestration/plan/${planId}/execute`);
    return response.data;
  }

  async getPlan(planId: string): Promise<any> {
    const response = await this.axios.get(`/api/v1/orchestration/plan/${planId}`);
    return response.data;
  }
}

export class AnalyticsResource extends BaseResource {
  async getDashboard(params?: { days?: number }): Promise<any> {
    const response = await this.axios.get('/api/v1/analytics/dashboard', { params });
    return response.data;
  }

  async getUserAnalytics(userId: string, params?: { period_type?: string }): Promise<any> {
    const response = await this.axios.get(`/api/v1/analytics/user/${userId}`, { params });
    return response.data;
  }

  async getAgentAnalytics(agentId: string, params?: { period_type?: string }): Promise<any> {
    const response = await this.axios.get(`/api/v1/analytics/agent/${agentId}`, { params });
    return response.data;
  }

  async recordMetric(params: Types.MetricParams): Promise<any> {
    const response = await this.axios.post('/api/v1/analytics/metrics/record', params);
    return response.data;
  }
}

export class SecurityResource extends BaseResource {
  async getReputation(agentId: string): Promise<Types.ReputationScore> {
    const response = await this.axios.get(`/api/v1/security/reputation/${agentId}`);
    return response.data;
  }

  async getFraudAlerts(params?: Types.FraudAlertParams): Promise<any> {
    const response = await this.axios.get('/api/v1/security/fraud-alerts', { params });
    return response.data;
  }

  async exportUserData(userId: string): Promise<any> {
    const response = await this.axios.post('/api/v1/security/gdpr/export', { user_id: userId });
    return response.data;
  }
}
