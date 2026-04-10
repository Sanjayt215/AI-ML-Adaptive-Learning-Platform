export async function apiFetch(url, options = {}) {
  const envBase = process.env.REACT_APP_API_BASE_URL?.trim();
  const isDev = process.env.NODE_ENV === 'development';
  const useProxy = isDev && !envBase;

  const buildUrl = (targetUrl) => {
    if (/^https?:\/\//.test(targetUrl)) {
      return targetUrl;
    }
    if (useProxy) {
      // Use relative URL so React proxy handles it
      return targetUrl;
    }
    const base = envBase || 'http://localhost:5000';
    return `${base}${targetUrl}`;
  };

  let response;
  try {
    response = await fetch(buildUrl(url), {
      credentials: 'include',
      ...options,
      headers: {
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    throw new Error('Cannot reach backend server. Start Python backend first on port 5000.');
  }

  const rawText = await response.text();
  let data = null;
  if (rawText) {
    try {
      data = JSON.parse(rawText);
    } catch {
      const cleaned = rawText.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
      if (cleaned.toLowerCase().startsWith('proxy error')) {
        throw new Error('React proxy could not reach the Flask backend. Run python app.py before npm start.');
      }
      throw new Error(cleaned || 'Server returned an invalid response.');
    }
  }

  if (!response.ok || (data && data.ok === false)) {
    throw new Error((data && data.error) || `Request failed with status ${response.status}`);
  }
  return data || { ok: response.ok };
}
