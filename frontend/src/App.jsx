import React, { useState, useEffect } from 'react';
import * as api from './api';
import { 
  MessageCircle, 
  Upload, 
  Search, 
  FileText, 
  Menu, 
  X, 
  Plus, 
  Send, 
  Eye, 
  Link, 
  Paperclip, 
  Trash2, 
  User, 
  Bot, 
  ExternalLink,
  Clock,
  Archive,
  MoreVertical
} from 'lucide-react';

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
  const [hoveredSession, setHoveredSession] = useState(null);

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
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    
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

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation(); // Prevent triggering the session load
    
    if (!window.confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
      return;
    }
    
    try {
      await api.deleteSession(sessionId);
      
      // If we're deleting the current session, clear the chat
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      
      // Reload sessions list
      loadSessions();
    } catch (error) {
      console.error('Error deleting session:', error);
      alert('Failed to delete conversation');
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-white shadow-sm overflow-hidden border-r border-gray-200`}>
        <div className="p-8 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
              <MessageCircle className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Positron Docs</h1>
              <p className="text-xs text-gray-500 font-medium">Retrieval Augmented Generation</p>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <button
            onClick={startNewChat}
            className="w-full mb-8 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 font-medium text-sm flex items-center justify-center space-x-2"
          >
            <Plus className="w-4 h-4 text-white" />
            <span>New Conversation</span>
          </button>
          
          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Recent Conversations
            </h3>
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {sessions.length === 0 ? (
                <p className="text-sm text-gray-400 italic py-4">No conversations yet</p>
              ) : (
                sessions.map(session => (
                  <button
                    key={session.id}
                    onClick={() => loadSessionMessages(session.id)}
                    onMouseEnter={() => setHoveredSession(session.id)}
                    onMouseLeave={() => setHoveredSession(null)}
                    className={`w-full text-left p-3 rounded-lg transition-all duration-150 group relative ${
                      currentSessionId === session.id 
                        ? 'bg-blue-50 border border-blue-200 text-blue-900' 
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1 min-w-0">
                        <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                          currentSessionId === session.id ? 'bg-blue-500' : 'bg-gray-300'
                        }`} />
                        <span className="text-sm font-medium truncate flex-1 leading-5 pr-2">{session.title}</span>
                      </div>
                      {(hoveredSession === session.id || currentSessionId === session.id) && (
                        <button
                          onClick={(e) => handleDeleteSession(session.id, e)}
                          className="p-1 hover:bg-red-100 rounded transition-colors duration-150 flex-shrink-0"
                          title="Delete conversation"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-red-500" />
                        </button>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
              >
                {sidebarOpen ? (
                  <X className="w-5 h-5 text-gray-600" />
                ) : (
                  <Menu className="w-5 h-5 text-gray-600" />
                )}
              </button>
              
              <nav className="flex space-x-1">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-2 ${
                    activeTab === 'chat' 
                      ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <MessageCircle className="w-4 h-4" />
                  <span>Chat</span>
                </button>
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-2 ${
                    activeTab === 'upload' 
                      ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  <span>Import</span>
                </button>
                <button
                  onClick={() => setActiveTab('search')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-2 ${
                    activeTab === 'search' 
                      ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Search className="w-4 h-4" />
                  <span>Search</span>
                </button>
                <button
                  onClick={() => setActiveTab('documents')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-2 ${
                    activeTab === 'documents' 
                      ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  <span>Documents</span>
                </button>
              </nav>
            </div>

            {stats && (
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <FileText className="w-3 h-3" />
                  <span>{stats.documents} documents</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Archive className="w-3 h-3" />
                  <span>{stats.vector_store?.total_chunks || 0} chunks</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          {activeTab === 'chat' && (
            <div className="flex flex-col h-full max-w-4xl mx-auto">
              <div className="flex-1 overflow-auto px-6 py-8 space-y-6">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center py-16">
                    <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                      <Eye className="w-8 h-8 text-blue-600" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 mb-3">How can I help you today?</h2>
                    <p className="text-gray-500 text-lg max-w-md mb-8">Ask questions about your documents and I'll provide answers based on your knowledge base.</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full">
                      <div className="bg-white border border-gray-200 rounded-xl p-6 hover:border-gray-300 transition-colors duration-200">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                          <FileText className="w-5 h-5 text-blue-600" />
                        </div>
                        <h3 className="font-medium text-gray-900 mb-2">Document Analysis</h3>
                        <p className="text-sm text-gray-500">Upload and analyze documents to extract insights and answers</p>
                      </div>
                      <div className="bg-white border border-gray-200 rounded-xl p-6 hover:border-gray-300 transition-colors duration-200">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                          <Search className="w-5 h-5 text-blue-600" />
                        </div>
                        <h3 className="font-medium text-gray-900 mb-2">Smart Search</h3>
                        <p className="text-sm text-gray-500">Search through your knowledge base with natural language</p>
                      </div>
                    </div>
                  </div>
                )}
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                  >
                    <div className={`max-w-3xl ${msg.role === 'user' ? 'ml-12' : 'mr-12'}`}>
                      <div className="flex items-start space-x-3 mb-2">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.role === 'user' ? 'bg-blue-500' : 'bg-gray-200'
                        }`}>
                          {msg.role === 'user' ? (
                            <User className="w-4 h-4 text-white" />
                          ) : (
                            <Bot className="w-4 h-4 text-gray-600" />
                          )}
                        </div>
                        <span className="text-xs font-medium text-gray-500 mt-2">
                          {msg.role === 'user' ? 'You' : 'Positron'}
                        </span>
                      </div>
                      
                      <div className={`p-4 rounded-xl ${
                        msg.role === 'user' 
                          ? 'bg-blue-500 text-white ml-11' 
                          : 'bg-white border border-gray-200 ml-11'
                      }`}>
                        <div className={`whitespace-pre-wrap leading-relaxed ${
                          msg.role === 'user' ? 'text-white' : 'text-gray-800'
                        }`}>
                          {msg.content}
                        </div>
                        
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <p className="text-sm font-medium mb-3 text-gray-600 flex items-center space-x-1">
                              <Link className="w-4 h-4" />
                              <span>Sources</span>
                            </p>
                            <div className="space-y-2">
                              {msg.sources.map((source, i) => (
                                <div key={i} className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                                  <p className="text-xs font-medium text-gray-600">
                                    {source.metadata.source} 
                                    {source.metadata.page && ` - Page ${source.metadata.page}`}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start animate-fadeIn">
                    <div className="max-w-3xl mr-12">
                      <div className="flex items-start space-x-3 mb-2">
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                          <Bot className="w-4 h-4 text-gray-600" />
                        </div>
                        <span className="text-xs font-medium text-gray-500 mt-2">Positron</span>
                      </div>
                      <div className="bg-white border border-gray-200 p-4 rounded-xl ml-11">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                          <span className="text-sm text-gray-500 ml-2">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="border-t border-gray-200 bg-white px-6 py-4">
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSendMessage()}
                    placeholder="Ask me anything about your documents..."
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={isLoading || !message.trim()}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 font-medium flex items-center space-x-2"
                  >
                    <Send className="w-4 h-4" />
                    <span>{isLoading ? 'Sending...' : 'Send'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="max-w-4xl mx-auto p-6">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Import Data</h2>
                <p className="text-gray-500">Upload documents or import web content to expand your knowledge base</p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">Document Upload</h3>
                  </div>
                  
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors duration-200">
                    <div className="space-y-4">
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto flex-shrink-0">
                        <Upload className="w-6 h-6 text-gray-400 flex-shrink-0" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">
                          {uploadFile ? `Selected: ${uploadFile.name}` : 'Choose files to upload'}
                        </p>
                        <p className="text-xs text-gray-500 mb-4">
                          PDF, TXT, and Markdown files supported
                        </p>
                        <input
                          type="file"
                          accept=".pdf,.txt,.md"
                          onChange={(e) => setUploadFile(e.target.files[0])}
                          className="hidden"
                          id="file-upload"
                        />
                        <label
                          htmlFor="file-upload"
                          className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 cursor-pointer text-sm font-medium"
                        >
                          <Paperclip className="w-4 h-4" />
                          <span>Browse Files</span>
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  {uploadFile && (
                    <div className="mt-4">
                      <button
                        onClick={handleFileUpload}
                        disabled={isLoading}
                        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 font-medium text-sm"
                      >
                        {isLoading ? 'Uploading...' : 'Upload Document'}
                      </button>
                    </div>
                  )}
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Link className="w-5 h-5 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">Import URL</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Website URL</label>
                      <input
                        type="url"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        placeholder="https://example.com/article"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                    </div>
                    
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={extractPdfs}
                          onChange={(e) => setExtractPdfs(e.target.checked)}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        />
                        <div>
                          <span className="text-sm font-medium text-gray-700">Extract PDFs from page</span>
                          <p className="text-xs text-gray-500">Automatically find and process PDF links</p>
                        </div>
                      </label>
                    </div>
                    
                    <button
                      onClick={handleUrlIngest}
                      disabled={!urlInput || isLoading}
                      className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 font-medium text-sm"
                    >
                      {isLoading ? 'Processing...' : 'Import URL'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'search' && (
            <div className="max-w-4xl mx-auto p-6">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Search Documents</h2>
                <p className="text-gray-500">Find specific information across your knowledge base</p>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                <div className="flex space-x-3">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSearch()}
                      placeholder="Search your documents..."
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <Search className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                  <button
                    onClick={handleSearch}
                    disabled={isLoading || !searchQuery.trim()}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
                  >
                    {isLoading ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </div>

              {searchResults.length === 0 && searchQuery && !isLoading && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <Search className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                  <p className="text-gray-500">No results found for "{searchQuery}". Try different keywords.</p>
                </div>
              )}

              <div className="space-y-4">
                {searchResults.map((result, idx) => (
                  <div key={idx} className="bg-white rounded-lg border border-gray-200 p-6 hover:border-gray-300 transition-colors duration-200">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <FileText className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">
                            {result.metadata.source}
                            {result.metadata.page && ` - Page ${result.metadata.page}`}
                          </p>
                          <p className="text-sm text-gray-500">Document</p>
                        </div>
                      </div>
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">
                        {(result.score * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-700 text-sm leading-relaxed">{result.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="max-w-5xl mx-auto p-6">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Document Library</h2>
                <p className="text-gray-500">Manage and organize your knowledge base</p>
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-16">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-6">
                    <FileText className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded yet</h3>
                  <p className="text-gray-500 mb-6">Start building your knowledge base by uploading documents</p>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 font-medium inline-flex items-center space-x-2"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Upload Documents</span>
                  </button>
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">
                      Documents ({documents.length})
                    </h3>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Document
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Chunks
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Uploaded
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {documents.map(doc => (
                          <tr key={doc.id} className="hover:bg-gray-50 transition-colors duration-150">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                                  <FileText className="w-4 h-4 text-blue-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                {doc.content_type}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {doc.num_chunks}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(doc.upload_date).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <button
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="text-red-600 hover:text-red-900 font-medium hover:bg-red-50 px-2 py-1 rounded transition-colors duration-200"
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
          )}
        </div>
      </div>
    </div>
  );
}

export default App;