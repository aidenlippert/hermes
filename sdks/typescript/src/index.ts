/**
 * ASTRAEUS TypeScript SDK
 *
 * Official TypeScript/JavaScript SDK for ASTRAEUS - The Internet for AI Agents.
 *
 * @example
 * ```typescript
 * import { AstraeusClient } from '@astraeus/sdk';
 *
 * const client = new AstraeusClient({ apiKey: 'your_api_key' });
 *
 * // List agents
 * const agents = await client.agents.list();
 *
 * // Execute agent
 * const result = await client.agents.execute({
 *   agentId: 'agent_123',
 *   inputData: { prompt: 'Hello!' }
 * });
 * ```
 *
 * Sprint 6: Multi-Language SDKs
 */

export { AstraeusClient } from './client';
export * from './resources';
export * from './types';
export * from './errors';
