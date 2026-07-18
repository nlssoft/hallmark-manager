import axios, { AxiosError } from "axios";
import type { FailedQueueItem, RetryRequestConfig } from "../types/frontedTypes/auth";
import { refresh } from "./auth";
import { notifyAuthFailure } from "../auth/events";

const apiConfig = {
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
};

export const api = axios.create(apiConfig);
export const authApi = axios.create(apiConfig);

const failedQueue: FailedQueueItem[] = [];
let isRefreshing: boolean = false;

function processQueue(error?: unknown) {
  if (error) {
    for (const { reject } of failedQueue) {
      reject(error);
    }
  } else {
    for (const { resolve } of failedQueue) {
      resolve();
    }
  }
  failedQueue.length = 0;
}

api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    if (!error.config) {
      return Promise.reject(error);
    }

    const originalRequest = error.config as RetryRequestConfig;

    const status = error.response?.status;
    if (status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      notifyAuthFailure();
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve,
          reject,
        });
      }).then(() => {
        return api(originalRequest);
      });
    }

    isRefreshing = true;
    try {
      await refresh();
      processQueue();
      return api(originalRequest);
    } catch (error) {
      processQueue(error);
      notifyAuthFailure();
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);
