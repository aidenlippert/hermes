/**
 * ASTRAEUS SDK Errors
 *
 * Sprint 6: Multi-Language SDKs
 */

export class AstraeusError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AstraeusError';
  }
}

export class AuthenticationError extends AstraeusError {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class APIError extends AstraeusError {
  public statusCode?: number;
  public response?: any;

  constructor(message: string, statusCode?: number, response?: any) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.response = response;
  }
}

export class RateLimitError extends AstraeusError {
  constructor(message: string) {
    super(message);
    this.name = 'RateLimitError';
  }
}

export class ValidationError extends AstraeusError {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}
