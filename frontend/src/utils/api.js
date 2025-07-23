const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const fetchHello = () =>
  fetch(`${BACKEND_URL}/api/hello`).then((res) => res.json());

export const uploadFile = (formData) =>
  fetch(`${BACKEND_URL}/api/upload`, {
    method: "POST",
    body: formData,
  }).then((res) => res.json());

export const pollStatus = (taskId) =>
  fetch(`${BACKEND_URL}/api/status/${taskId}`).then((res) => res.json());

export const clearSession = (sessionId) =>
  navigator.sendBeacon(`${BACKEND_URL}/api/clear`, JSON.stringify({ session_id: sessionId }));
