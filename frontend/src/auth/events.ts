export let onAuthFailure: (() => void) | null = null;
export const authChannel = new BroadcastChannel("auth");

export function registerAuthFailureHandler(handler: () => void) {
  onAuthFailure = handler;
}

export function handleAuthfailure() {
  onAuthFailure?.();
}

export function notifyAuthFailure() {
  onAuthFailure?.();
  authChannel.postMessage({
    type: "logout",
  });
}
