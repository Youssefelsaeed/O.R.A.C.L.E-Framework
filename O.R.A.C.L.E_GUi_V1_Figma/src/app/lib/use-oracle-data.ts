import { useCallback, useEffect, useState } from "react";
import {
  fetchDashboardSummary,
  fetchEvolution,
  type ApiResult,
  type DashboardSummary,
} from "@/app/lib/api";

export function useDashboardSummary() {
  const [result, setResult] = useState<ApiResult<DashboardSummary>>({
    data: null,
    offline: false,
  });
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const res = await fetchDashboardSummary();
    setResult(res);
    setLoading(false);
    return res;
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { ...result, loading, refresh };
}

export function useEvolutionData() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [offline, setOffline] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const res = await fetchEvolution();
    setData(res.data);
    setOffline(res.offline);
    setLoading(false);
    return res;
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, offline, loading, refresh };
}
