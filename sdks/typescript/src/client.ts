/**
 * ASTRAEUS TypeScript SDK - Main Client
 *
 * Sprint 6: Multi-Language SDKs
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import {
  AgentsResource,
  ContractsResource,
  PaymentsResource,
  OrchestrationResource,
  AnalyticsResource,
  SecurityResource
} from './resources';
import {
  AstraeusError,
  AuthenticationError,
  APIError,
  RateLimitError
} from './errors';

export interface AstraeusClientConfig {
  apiKey: string;
  baseURL?: string;
  timeout?: number;
}

export class AstraeusClient {
  private axios: AxiosInstance;
  public agents: AgentsResource;
  public contracts: ContractsResource;
  public payments: PaymentsResource;
  public orchestration: OrchestrationResource;
  public analytics: AnalyticsResource;
  public security: SecurityResource;

  constructor(config: AstraeusClientConfig) {
    const {
      apiKey,
      baseURL = 'https://api.astraeus.ai',
      timeout = 30000
    } = config;

    this.axios = axios.create({
      baseURL,
      timeout,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'astraeus-typescript/1.0.0'
      }
    });

    // Response interceptor for error handling
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const { status, data } = error.response;

          if (status === 401) {
            throw new AuthenticationError('Invalid API key');
          } else if (status === 429) {
            throw new RateLimitError('Rate limit exceeded');
          } else {
            throw new APIError(
              `API error: ${status}`,
              status,
              data
            );
          }
        } else if (error.request) {
          throw new AstraeusError('No response from server');
        } else {
          throw new AstraeusError(`Request failed: ${error.message}`);
        }
      }
    );

    // Initialize resources
    this.agents = new AgentsResource(this.axios);
    this.contracts = new ContractsResource(this.axios);
    this.payments = new PaymentsResource(this.axios);
    this.orchestration = new OrchestrationResource(this.axios);
    this.analytics = new AnalyticsResource(this.axios);
    this.security = new SecurityResource(this.axios);
  }
}
