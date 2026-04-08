/**
 * Error classes for Cerebrum SDK
 */

/** Base error class for Cerebrum SDK */
export class CerebrumError extends Error {
  statusCode?: number;
  
  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'CerebrumError';
    this.statusCode = statusCode;
  }
}

/** Authentication error - invalid or missing API key */
export class AuthenticationError extends CerebrumError {
  constructor(message: string = 'Invalid or missing API key') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

/** Rate limit error - too many requests */
export class RateLimitError extends CerebrumError {
  constructor(message: string = 'Rate limit exceeded. Upgrade your plan.') {
    super(message, 429);
    this.name = 'RateLimitError';
  }
}

/** Block not found error */
export class BlockNotFoundError extends CerebrumError {
  constructor(message: string = 'Block not found') {
    super(message, 404);
    this.name = 'BlockNotFoundError';
  }
}

/** Execution error - block execution failed */
export class ExecutionError extends CerebrumError {
  constructor(message: string = 'Execution failed') {
    super(message, 500);
    this.name = 'ExecutionError';
  }
}

/** Validation error - invalid request */
export class ValidationError extends CerebrumError {
  constructor(message: string = 'Validation failed') {
    super(message, 400);
    this.name = 'ValidationError';
  }
}
