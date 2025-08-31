import React, { useState, useEffect } from 'react';
import * as api from './api';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [uploadFile, setUploadFile] = useState(null);
  const [urlInput, setUrlInput] = useState('');
  const [extractPdfs, setExtractPdfs] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    loadSessions();
    loadDocuments();
    loadStats();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const data = await api.getSessionMessages(sessionId);
      setMessages(data);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);

    try {
      const response = await api.sendMessage(message, currentSessionId);
      
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setCurrentSessionId(response.session_id);
      loadSessions();
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    
    setIsLoading(true);
    try {
      await api.uploadDocument(uploadFile);
      setUploadFile(null);
      loadDocuments();
      loadStats();
      alert('Document uploaded successfully!');
    } catch (error) {
      console.error('Error uploading document:', error);
      alert('Error uploading document');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUrlIngest = async () => {
    if (!urlInput.trim()) return;
    
    setIsLoading(true);
    try {
      await api.ingestUrl(urlInput, extractPdfs);
      setUrlInput('');
      setExtractPdfs(false);
      loadDocuments();
      loadStats();
      alert('URL ingested successfully!');
    } catch (error) {
      console.error('Error ingesting URL:', error);
      alert('Error ingesting URL');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const results = await api.searchDocuments(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.deleteDocument(docId);
      loadDocuments();
      loadStats();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-white shadow-lg overflow-hidden`}>
        <div className="p-4 border-b">
          <h2 className="text-xl font-bold text-gray-800">RAG Interface</h2>
        </div>
        
        <div className="p-4">
          <button
            onClick={startNewChat}
            className="w-full mb-4 p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            New Chat
          </button>
          
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-600">Recent Sessions</h3>
            {sessions.map(session => (
              <button
                key={session.id}
                onClick={() => loadSessionMessages(session.id)}
                className={`w-full text-left p-2 rounded hover:bg-gray-100 ${
                  currentSessionId === session.id ? 'bg-gray-100' : ''
                }`}
              >
                <div className="flex items-center">
                  <span className="text-sm truncate">{session.title}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm p-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded"
          >
            {sidebarOpen ? 'X' : '☰'}
          </button>
          
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 rounded ${activeTab === 'chat' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 rounded ${activeTab === 'upload' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
            >
              Upload
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`px-4 py-2 rounded ${activeTab === 'search' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
            >
              Search
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-4 py-2 rounded ${activeTab === 'documents' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
            >
              Documents
            </button>
          </div>

          {stats && (
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Docs: {stats.documents}</span>
              <span>Chunks: {stats.vector_store.total_chunks}</span>
            </div>
          )}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'chat' && (
            <div className="flex flex-col h-full">
              <div className="flex-1 overflow-auto mb-4 space-y-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-3xl p-4 rounded-lg ${
                        msg.role === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-white shadow'
                      }`}
                    >
                      <div>{msg.content}</div>
                      
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <p className="text-sm font-semibold mb-2">Sources:</p>
                          {msg.sources.map((source, i) => (
                            <div key={i} className="text-xs mb-2">
                              <p className="text-gray-600">
                                {source.metadata.source} 
                                {source.metadata.page && ` - Page ${source.metadata.page}`}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white shadow p-4 rounded-lg">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading}
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
                >
                  Send
                </button>
              </div>
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">Upload Document</h3>
                <input
                  type="file"
                  accept=".pdf,.txt,.md"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  className="mb-4"
                />
                <button
                  onClick={handleFileUpload}
                  disabled={!uploadFile || isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                >
                  Upload
                </button>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">Ingest URL</h3>
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="Enter URL..."
                  className="w-full p-2 border rounded mb-4"
                />
                <label className="flex items-center mb-4">
                  <input
                    type="checkbox"
                    checked={extractPdfs}
                    onChange={(e) => setExtractPdfs(e.target.checked)}
                    className="mr-2"
                  />
                  Extract and ingest PDFs from page
                </label>
                <button
                  onClick={handleUrlIngest}
                  disabled={!urlInput || isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                >
                  Ingest
                </button>
              </div>
            </div>
          )}

          {activeTab === 'search' && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-white p-6 rounded-lg shadow mb-6">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="Search documents..."
                    className="flex-1 p-2 border rounded"
                  />
                  <button
                    onClick={handleSearch}
                    disabled={isLoading}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Search
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {searchResults.map((result, idx) => (
                  <div key={idx} className="bg-white p-4 rounded-lg shadow">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm text-gray-600">
                        {result.metadata.source}
                        {result.metadata.page && ` - Page ${result.metadata.page}`}
                      </span>
                      <span className="text-sm font-semibold text-blue-600">
                        Score: {(result.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-gray-800">{result.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Filename
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Chunks
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Upload Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {documents.map(doc => (
                      <tr key={doc.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-gray-900">{doc.filename}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {doc.content_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {doc.num_chunks}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(doc.upload_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App
