import { useCallback } from "react";
import { useAuth } from "@clerk/nextjs";

import * as api from "@/lib/api";

export function useApiClient() {
  const { getToken, userId, isLoaded } = useAuth();
  const uid = userId ?? undefined;

  const getCases = useCallback(
    (titleSearch?: string) =>
      getToken().then((token) => api.getCases(token, uid, titleSearch)),
    [getToken, uid],
  );

  const deleteCase = useCallback(
    (id: string) =>
      getToken().then((token) => api.deleteCase(id, uid, token)),
    [getToken, uid],
  );

  const getCase = useCallback(
    (id: string) =>
      getToken().then((token) => api.getCase(id, uid, token)),
    [getToken, uid],
  );

  const postAnalyzeStream = useCallback(
    (
      input: api.AnalyzeFormInput,
      signal: AbortSignal,
      onSseData: (payload: api.SseAnalyzePayload) => void,
      onError: (message: string) => void,
    ) =>
      getToken().then((token) =>
        api.postAnalyzeStream(input, uid, token, signal, onSseData, onError),
      ),
    [getToken, uid],
  );

  return { isLoaded, getCases, deleteCase, getCase, postAnalyzeStream };
}
