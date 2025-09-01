import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const ingestUrl = async (url, extractPdfs = false) => {
  const response = await api.post('/ingest_url', {
    url,
    extract_pdfs: extractPdfs,
  });
  return response.data;
};

export const sendMessage = async (message, sessionId = null, useContext = true, topK = 5) => {
  const response = await api.post('/chat', {
    message,
    session_id: sessionId,
    use_context: useContext,
    top_k: topK,
  });
  return response.data;
};

export const getSessions = async () => {
  const response = await api.get('/sessions');
  return response.data;
};

export const getSessionMessages = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/messages`);
  return response.data;
};

export const deleteSession = async (sessionId) => {
  const response = await api.delete(`/sessions/${sessionId}`);
  return response.data;
};

export const searchDocuments = async (query, topK = 5) => {
  const response = await api.post('/search', {
    query,
    top_k: topK,
  });
  return response.data;
};

export const getDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

export const deleteDocument = async (docId) => {
  const response = await api.delete(`/documents/${docId}`);
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};