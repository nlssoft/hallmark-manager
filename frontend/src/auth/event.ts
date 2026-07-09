export let onAuthFailure: (() => void) | null = null;

export function registerAuthFailureHandler(handler: () => void) {
  onAuthFailure = handler;
}

export function notifyAuthFailure() {
  onAuthFailure?.();
}
