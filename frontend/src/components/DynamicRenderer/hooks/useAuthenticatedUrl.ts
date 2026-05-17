import { useState, useEffect } from "react";
import { apiUrl, getToken } from "../../../api/client";

/**
 * Fetches a backend file path with the JWT Authorization header and returns a
 * blob URL safe for <img>, <audio>, and <iframe>. Using fetch() + blob avoids
 * the need for getToken() to be non-null at render time (which can happen when
 * AuthContext clears an expired token after mount). The Authorization header is
 * sent the same way as every other API call in client.ts.
 */
export function useAuthenticatedUrl(path: string | undefined): {
  url: string | undefined;
  loading: boolean;
  error: boolean;
} {
  const [url, setUrl] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(!!path);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!path) return;

    let revoked = false;
    let blobUrl: string | undefined;

    setLoading(true);
    setError(false);
    setUrl(undefined);

    const token = getToken();
    fetch(apiUrl(path), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        blobUrl = URL.createObjectURL(blob);
        if (!revoked) setUrl(blobUrl);
      })
      .catch(() => {
        if (!revoked) setError(true);
      })
      .finally(() => {
        if (!revoked) setLoading(false);
      });

    return () => {
      revoked = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [path]);

  return { url, loading, error };
}
