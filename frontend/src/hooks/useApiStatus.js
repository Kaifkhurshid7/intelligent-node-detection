/**
 * Custom hook for monitoring backend API health.
 *
 * Checks connectivity on mount and exposes the current status
 * for UI indicators (online/offline/checking).
 */

import { useState, useEffect } from "react";
import { checkHealth } from "../services/api";
import { API_STATUS } from "../constants";

export function useApiStatus() {
  const [status, setStatus] = useState(API_STATUS.CHECKING);

  useEffect(() => {
    const check = async () => {
      const healthy = await checkHealth();
      setStatus(healthy ? API_STATUS.CONNECTED : API_STATUS.DISCONNECTED);
    };
    check();
  }, []);

  return status;
}
