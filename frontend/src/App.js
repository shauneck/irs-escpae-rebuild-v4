import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Header Component
const Header = ({ activeSection, setActiveSection }) => {
  return (
    <header className="bg-navy-900 text-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-2xl font-bold text-emerald-400">
              IRS Escape Plan
            </div>
            <div className="hidden md:block text-sm text-gray-300">
              Your Path to Tax Freedom
            </div>
          </div>
          
          <nav className="hidden md:flex space-x-6">
            {['courses', 'taxbot', 'premium-tools', 'tools', 'glossary', 'marketplace'].map((section) => (
              <button
                key={section}
                onClick={() => setActiveSection(section)}
                className={`capitalize transition-colors duration-200 ${
                  activeSection === section
                    ? 'text-emerald-400 border-b-2 border-emerald-400'
                    : 'text-gray-300 hover:text-emerald-400'
                }`}
              >
                {section}
              </button>
            ))}
          </nav>
          
          <div className="flex items-center space-x-4">
            <button className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
              Get Started Free
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

// TaxBot AI Assistant Component
const TaxBotSection = () => {
  const [chatThreads, setChatThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredThreads, setFilteredThreads] = useState([]);

  useEffect(() => {
    loadChatThreads();
  }, []);

  useEffect(() => {
    if (searchQuery) {
      const filtered = chatThreads.filter(thread => 
        thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        thread.messages.some(msg => 
          msg.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
          msg.response.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
      setFilteredThreads(filtered);
    } else {
      setFilteredThreads(chatThreads);
    }
  }, [searchQuery, chatThreads]);

  const loadChatThreads = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/users/default_user/chat-threads`);
      if (response.ok) {
        const threads = await response.json();
        setChatThreads(threads);
        setFilteredThreads(threads);
      }
    } catch (error) {
      console.error('Failed to load chat threads:', error);
    }
  };

  const createNewThread = async () => {
    const newThread = {
      id: Date.now().toString(),
      user_id: 'default_user',
      title: 'New Strategy Discussion',
      messages: [],
      created_at: new Date().toISOString(),
      last_updated: new Date().toISOString(),
      is_starred: false
    };

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/users/default_user/chat-threads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newThread)
      });

      if (response.ok) {
        const thread = await response.json();
        setChatThreads([thread, ...chatThreads]);
        setCurrentThread(thread);
      }
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !currentThread) return;

    setIsLoading(true);
    const message = {
      id: Date.now().toString(),
      user_id: 'default_user',
      message: newMessage,
      response: '',
      timestamp: new Date().toISOString(),
      is_starred: false,
      context_modules: [],
      context_glossary: []
    };

    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/users/default_user/chat-threads/${currentThread.id}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(message)
        }
      );

      if (response.ok) {
        const updatedMessage = await response.json();
        const updatedThread = {
          ...currentThread,
          messages: [...currentThread.messages, updatedMessage],
          last_updated: new Date().toISOString()
        };
        setCurrentThread(updatedThread);
        
        // Update threads list
        setChatThreads(threads => 
          threads.map(t => t.id === currentThread.id ? updatedThread : t)
        );
        
        setNewMessage('');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMessageStar = async (messageId) => {
    if (!currentThread) return;

    try {
      await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/users/default_user/chat-threads/${currentThread.id}/messages/${messageId}/star`,
        { method: 'PUT' }
      );

      const updatedThread = {
        ...currentThread,
        messages: currentThread.messages.map(msg =>
          msg.id === messageId ? { ...msg, is_starred: !msg.is_starred } : msg
        )
      };
      setCurrentThread(updatedThread);
    } catch (error) {
      console.error('Failed to star message:', error);
    }
  };

  const exportToPDF = () => {
    if (!currentThread) return;
    
    const content = currentThread.messages.map(msg => 
      `Q: ${msg.message}\nA: ${msg.response}\n\n`
    ).join('');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentThread.title}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!currentThread) return;
    
    const content = currentThread.messages.map(msg => 
      `Q: ${msg.message}\nA: ${msg.response}\n\n`
    ).join('');
    
    navigator.clipboard.writeText(content);
    alert('Chat transcript copied to clipboard!');
  };

  const renderGlossaryLinks = (text) => {
    const glossaryTerms = ['REPS', 'QBI', 'Cost Segregation', 'W-2 Income', 'Depreciation'];
    let linkedText = text;
    
    glossaryTerms.forEach(term => {
      const regex = new RegExp(`\\b${term}\\b`, 'gi');
      linkedText = linkedText.replace(regex, `<span class="glossary-link" title="Click to view definition">${term}</span>`);
    });
    
    return <div dangerouslySetInnerHTML={{ __html: linkedText }} />;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-navy-900 mb-2">
            🧠 QGPT - AI Tax Strategist
          </h1>
          <p className="text-xl text-gray-600">
            Advanced tax strategy guidance from The IRS Escape Plan by Quantus Group
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[80vh]">
          {/* Chat Threads Sidebar */}
          <div className="lg:col-span-1 bg-white rounded-xl shadow-lg p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-navy-900">My Strategy Notes</h2>
              <button
                onClick={createNewThread}
                className="bg-emerald-500 text-white p-2 rounded-lg hover:bg-emerald-600 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            {/* Search */}
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Thread List */}
            <div className="space-y-2">
              {filteredThreads.map((thread) => (
                <div
                  key={thread.id}
                  onClick={() => setCurrentThread(thread)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentThread?.id === thread.id
                      ? 'bg-emerald-100 border-emerald-500 border'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm text-navy-900 truncate">
                      {thread.title}
                    </h3>
                    {thread.is_starred && (
                      <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(thread.last_updated).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-3 bg-white rounded-xl shadow-lg overflow-hidden flex flex-col">
            {currentThread ? (
              <>
                {/* Chat Header */}
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold">{currentThread.title}</h2>
                    <div className="flex space-x-2">
                      <button
                        onClick={exportToPDF}
                        className="bg-blue-400 hover:bg-blue-300 p-2 rounded-lg transition-colors"
                        title="Export as PDF"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </button>
                      <button
                        onClick={copyToClipboard}
                        className="bg-blue-400 hover:bg-blue-300 p-2 rounded-lg transition-colors"
                        title="Copy to Clipboard"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {currentThread.messages.map((message) => (
                    <div key={message.id} className="space-y-4">
                      {/* User Message */}
                      <div className="flex justify-end">
                        <div className="bg-emerald-500 text-white p-3 rounded-lg max-w-md">
                          <p>{message.message}</p>
                        </div>
                      </div>

                      {/* AI Response */}
                      <div className="flex justify-start">
                        <div className="bg-gray-100 p-4 rounded-lg max-w-2xl">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center">
                              <span className="text-2xl mr-2">🤖</span>
                              <span className="font-bold text-navy-900">TaxBot</span>
                            </div>
                            <button
                              onClick={() => toggleMessageStar(message.id)}
                              className="text-gray-400 hover:text-yellow-500 transition-colors"
                            >
                              <svg className={`w-4 h-4 ${message.is_starred ? 'text-yellow-500 fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.196-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                              </svg>
                            </button>
                          </div>
                          
                          <div className="text-gray-700 mb-3">
                            {renderGlossaryLinks(message.response)}
                          </div>

                          {/* Context Links */}
                          {(message.context_modules.length > 0 || message.context_glossary.length > 0) && (
                            <div className="border-t pt-3 mt-3">
                              <p className="text-sm font-medium text-gray-600 mb-2">Related Resources:</p>
                              <div className="flex flex-wrap gap-2">
                                {message.context_modules.map((module, idx) => (
                                  <span key={idx} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                    📚 {module.replace('-', ' ')}
                                  </span>
                                ))}
                                {message.context_glossary.map((term, idx) => (
                                  <span key={idx} className="bg-teal-100 text-teal-800 text-xs px-2 py-1 rounded-full">
                                    💡 {term}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 p-4 rounded-lg">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">🤖</span>
                          <span className="text-gray-600">TaxBot is thinking...</span>
                          <div className="ml-2 flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Message Input */}
                <div className="border-t p-4">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Ask TaxBot about tax strategies, REPS qualification, offset planning..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      disabled={isLoading}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={isLoading || !newMessage.trim()}
                      className="bg-emerald-500 text-white px-6 py-2 rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Send
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    💡 Try asking: "How do I qualify for REPS?" or "What's the best W-2 offset strategy?"
                  </p>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <span className="text-6xl mb-4 block">🤖</span>
                  <h2 className="text-2xl font-bold text-navy-900 mb-2">Welcome to TaxBot</h2>
                  <p className="text-gray-600 mb-4">Select a conversation or start a new one to get personalized tax strategy guidance</p>
                  <button
                    onClick={createNewThread}
                    className="bg-emerald-500 text-white px-6 py-3 rounded-lg hover:bg-emerald-600 transition-colors"
                  >
                    Start New Conversation
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .glossary-link {
          color: #0d9488;
          background-color: #ccfbf1;
          padding: 2px 6px;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
          border-bottom: 1px dotted #0d9488;
        }
        .glossary-link:hover {
          background-color: #99f6e4;
        }
      `}</style>
    </div>
  );
};

// Hero Section Component
const HeroSection = () => {
  return (
    <section className="bg-gradient-to-br from-navy-900 via-navy-800 to-emerald-900 text-white py-20">
      <div className="container mx-auto px-6 text-center">
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          Escape IRS Problems
          <span className="block text-emerald-400">Forever</span>
        </h1>
        <p className="text-xl md:text-2xl mb-8 text-gray-300 max-w-3xl mx-auto">
          Master the strategies used by tax professionals to minimize your tax burden 
          and resolve IRS issues permanently.
        </p>
        <div className="flex flex-col md:flex-row justify-center space-y-4 md:space-y-0 md:space-x-6">
          <button className="bg-emerald-500 hover:bg-emerald-600 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors duration-200">
            Start Free Primer Course
          </button>
          <button className="border-2 border-white text-white hover:bg-white hover:text-navy-900 px-8 py-4 rounded-lg text-lg font-semibold transition-colors duration-200">
            View All Courses
          </button>
        </div>
      </div>
    </section>
  );
};

// Course Card Component
const CourseCard = ({ course, onCourseClick }) => {
  return (
    <div 
      className="group cursor-pointer transform transition-all duration-300 hover:scale-105"
      onClick={() => onCourseClick(course)}
    >
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="relative">
          <img 
            src={course.thumbnail_url} 
            alt={course.title}
            className="w-full h-48 object-cover"
          />
          <div className="absolute top-4 left-4">
            {course.is_free ? (
              <span className="bg-emerald-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                FREE
              </span>
            ) : (
              <span className="bg-navy-900 text-white px-3 py-1 rounded-full text-sm font-semibold">
                PREMIUM
              </span>
            )}
          </div>
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="bg-white rounded-full p-4">
                <svg className="w-8 h-8 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <h3 className="text-xl font-bold text-navy-900 mb-3">{course.title}</h3>
          <p className="text-gray-600 mb-4 line-clamp-3">{course.description}</p>
          
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>{course.total_lessons} lessons</span>
            <span>{course.estimated_hours}h total</span>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-2 rounded-lg transition-colors duration-200">
              {course.is_free ? 'Start Free Course' : 'Learn More'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Course Viewer Component
const CourseViewer = ({ course, onBack }) => {
  const [currentLesson, setCurrentLesson] = useState(0);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [quizResults, setQuizResults] = useState([]);
  const [showQuizResults, setShowQuizResults] = useState(false);
  const [userXP, setUserXP] = useState(0);
  const [showGlossary, setShowGlossary] = useState(false);
  const [glossaryTerms, setGlossaryTerms] = useState([]);
  
  const [glossaryXP, setGlossaryXP] = useState(0);
  const [viewedGlossaryTerms, setViewedGlossaryTerms] = useState(new Set());
  
  if (!course || !course.lessons) return null;
  
  const lesson = course.lessons[currentLesson];
  
  useEffect(() => {
    fetchQuizQuestions();
    fetchGlossaryTerms();
    
    // Load saved XP from localStorage
    try {
      const savedGlossaryXP = localStorage.getItem('glossaryXP');
      const savedViewedTerms = localStorage.getItem('viewedGlossaryTerms');
      
      if (savedGlossaryXP) {
        setGlossaryXP(parseInt(savedGlossaryXP, 10) || 0);
      }
      
      if (savedViewedTerms) {
        const terms = JSON.parse(savedViewedTerms);
        setViewedGlossaryTerms(new Set(terms));
      }
    } catch (error) {
      console.warn('Could not load XP from localStorage:', error);
    }
  }, [course.id, lesson.order_index]);
  
  const fetchQuizQuestions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/courses/${course.id}/quiz?module_id=${lesson.order_index}`);
      const questions = await response.json();
      setQuizQuestions(questions);
    } catch (error) {
      console.error('Error fetching quiz questions:', error);
    }
  };
  
  const fetchGlossaryTerms = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/glossary`);
      const terms = await response.json();
      setGlossaryTerms(terms);
    } catch (error) {
      console.error('Error fetching glossary terms:', error);
    }
  };
  
  const startQuiz = () => {
    setShowQuiz(true);
    setCurrentQuestion(0);
    setSelectedAnswer('');
    setQuizResults([]);
    setShowQuizResults(false);
  };
  
  const submitAnswer = async () => {
    if (!selectedAnswer) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/quiz/submit?course_id=${course.id}&question_id=${quizQuestions[currentQuestion].id}&answer=${selectedAnswer}`, {
        method: 'POST'
      });
      const result = await response.json();
      
      const newResult = {
        ...result,
        question: quizQuestions[currentQuestion].question,
        selectedAnswer,
        correctAnswer: quizQuestions[currentQuestion].correct_answer
      };
      
      setQuizResults([...quizResults, newResult]);
      
      if (result.correct) {
        setUserXP(userXP + result.points);
      }
      
      if (currentQuestion < quizQuestions.length - 1) {
        setCurrentQuestion(currentQuestion + 1);
        setSelectedAnswer('');
      } else {
        setShowQuizResults(true);
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };
  
  const getGlossaryTerm = (termName) => {
    return glossaryTerms.find(term => term.term.toLowerCase() === termName.toLowerCase());
  };
  
  const openGlossary = (termName) => {
    const term = getGlossaryTerm(termName);
    if (term) {
      setShowGlossary(term);
      
      // Award XP for first-time viewing with better tracking
      const termKey = `${term.id}_${course.id}_${lesson.order_index}`;
      if (!viewedGlossaryTerms.has(termKey)) {
        const newViewedTerms = new Set([...viewedGlossaryTerms, termKey]);
        setViewedGlossaryTerms(newViewedTerms);
        setGlossaryXP(glossaryXP + 5); // 5 XP per new term viewed
        
        // Store in localStorage for persistence
        try {
          localStorage.setItem('viewedGlossaryTerms', JSON.stringify([...newViewedTerms]));
          localStorage.setItem('glossaryXP', String(glossaryXP + 5));
        } catch (error) {
          console.warn('Could not save XP to localStorage:', error);
        }
      }
    }
  };
  
  // Enhanced content renderer with improved term matching and popover functionality
  const renderContentWithGlossary = (content) => {
    let processedContent = content;
    const processedTerms = new Set(); // Track which terms we've already processed
    
    // Create a comprehensive term map including variations
    const termVariations = new Map();
    glossaryTerms.forEach(term => {
      const baseTerm = term.term.toLowerCase();
      termVariations.set(baseTerm, term);
      
      // Add common variations
      if (baseTerm.endsWith('s')) {
        // Plural to singular
        termVariations.set(baseTerm.slice(0, -1), term);
      } else {
        // Singular to plural
        termVariations.set(baseTerm + 's', term);
      }
      
      // Add specific variations for known terms
      const variations = {
        'cpa': ['cpas', 'cpa'],
        'strategist': ['strategists', 'strategist', 'tax strategist', 'tax strategists'],
        'entity planning': ['entity structure', 'entity type'],
        'asset location': ['asset placement'],
        'opportunity zones': ['opportunity zone'],
        'reps': ['real estate professional', 'real estate professional status'],
        'str': ['short-term rental', 'short-term rentals'],
        'qof': ['qualified opportunity fund', 'qualified opportunity funds']
      };
      
      Object.entries(variations).forEach(([key, vars]) => {
        if (baseTerm.includes(key) || key.includes(baseTerm)) {
          vars.forEach(variation => {
            termVariations.set(variation.toLowerCase(), term);
          });
        }
      });
    });
    
    // Process each term variation
    termVariations.forEach((glossaryTerm, searchTerm) => {
      // Create case-insensitive regex pattern for bolded terms
      const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const boldPattern = new RegExp(`\\*\\*${escapedTerm}\\*\\*`, 'gi');
      let isFirstOccurrence = true;
      
      processedContent = processedContent.replace(boldPattern, (match) => {
        const termKey = glossaryTerm.term.toLowerCase();
        if (isFirstOccurrence && !processedTerms.has(termKey)) {
          // First occurrence - make it clickable with teal pill styling
          processedTerms.add(termKey);
          isFirstOccurrence = false;
          return `<span id="glossary-${termKey.replace(/\s+/g, '-')}" class="glossary-term" data-term="${glossaryTerm.term}" title="Click to view definition">${glossaryTerm.term}</span>`;
        } else {
          // Subsequent occurrences - subtle link back to first instance
          return `<span class="glossary-repeat" onclick="document.getElementById('glossary-${termKey.replace(/\s+/g, '-')}')?.scrollIntoView({behavior: 'smooth', block: 'center'}); const elem = document.getElementById('glossary-${termKey.replace(/\s+/g, '-')}'); if(elem) { elem.style.backgroundColor='#fef3c7'; setTimeout(() => elem.style.backgroundColor='', 2000); }" title="Jump to first occurrence">${match.replace(/\*\*/g, '')}</span>`;
        }
      });
    });
    
    return processedContent;
  };
  
  // Handle inline glossary clicks with improved event handling
  const handleContentClick = (e) => {
    if (e.target.classList.contains('glossary-term')) {
      e.preventDefault();
      e.stopPropagation();
      const termName = e.target.dataset.term;
      if (termName) {
        openGlossary(termName);
      }
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Course Header */}
      <div className="bg-navy-900 text-white py-8">
        <div className="container mx-auto px-6">
          <button 
            onClick={onBack}
            className="flex items-center text-emerald-400 hover:text-emerald-300 mb-4 transition-colors duration-200"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Courses
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">{course.title}</h1>
              <p className="text-gray-300">{course.description}</p>
            </div>
            <div className="text-right">
              <div className="bg-emerald-500 text-white px-4 py-2 rounded-lg">
                <div className="text-sm">Quiz XP</div>
                <div className="text-2xl font-bold">{userXP}</div>
              </div>
              <div className="bg-blue-500 text-white px-4 py-2 rounded-lg mt-2">
                <div className="text-sm">Glossary XP</div>
                <div className="text-xl font-bold">{glossaryXP}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="container mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Main Content */}
          <div className="lg:w-2/3">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              {/* Lesson Header with XP Badge */}
              <div className="bg-emerald-50 border-b border-emerald-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center mb-2">
                      <span className="bg-emerald-500 text-white text-sm px-3 py-1 rounded-full mr-3">
                        XP Available: {lesson.xp_available || 150}
                      </span>
                      <span className="text-emerald-700 font-semibold">
                        {lesson.description}
                      </span>
                    </div>
                    <h2 className="text-2xl font-bold text-navy-900">{lesson.title}</h2>
                  </div>
                  <div className="flex space-x-3">
                    {lesson.order_index === 1 ? (
                      <>
                        <button
                          onClick={() => openGlossary('Tax Planning')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Tax Planning
                        </button>
                        <button
                          onClick={() => openGlossary('W-2 Income')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 W-2 Income
                        </button>
                        <button
                          onClick={() => openGlossary('CPA vs Strategist')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 CPA vs Strategist
                        </button>
                      </>
                    ) : lesson.order_index === 2 ? (
                      <>
                        <button
                          onClick={() => openGlossary('Entity Planning')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Entity Planning
                        </button>
                        <button
                          onClick={() => openGlossary('Income Shifting')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Income Shifting
                        </button>
                        <button
                          onClick={() => openGlossary('Timing Arbitrage')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Timing Arbitrage
                        </button>
                        <button
                          onClick={() => openGlossary('Asset Location')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Asset Location
                        </button>
                        <button
                          onClick={() => openGlossary('Strategic Deductions')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Strategic Deductions
                        </button>
                        <button
                          onClick={() => openGlossary('Exit Structuring')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Exit Structuring
                        </button>
                      </>
                    ) : lesson.order_index === 3 ? (
                      <>
                        <button
                          onClick={() => openGlossary('Qualified Opportunity Fund')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 QOF
                        </button>
                        <button
                          onClick={() => openGlossary('Bonus Depreciation')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Bonus Depreciation
                        </button>
                        <button
                          onClick={() => openGlossary('REPS')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 REPS
                        </button>
                        <button
                          onClick={() => openGlossary('Depreciation Offset')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Depreciation Offset
                        </button>
                        <button
                          onClick={() => openGlossary('STR')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 STR
                        </button>
                      </>
                    ) : lesson.order_index === 4 ? (
                      <>
                        <button
                          onClick={() => openGlossary('AGI')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 AGI
                        </button>
                        <button
                          onClick={() => openGlossary('Deduction Bandwidth')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Deduction Bandwidth
                        </button>
                        <button
                          onClick={() => openGlossary('Income Type Stack')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Income Type Stack
                        </button>
                        <button
                          onClick={() => openGlossary('Entity Exposure')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Entity Exposure
                        </button>
                      </>
                    ) : lesson.order_index === 5 ? (
                      <>
                        <button
                          onClick={() => openGlossary('Tax Exposure')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Tax Exposure
                        </button>
                        <button
                          onClick={() => openGlossary('Lever Hierarchy')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Lever Hierarchy
                        </button>
                        <button
                          onClick={() => openGlossary('Personalized Planning')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Personalized Planning
                        </button>
                        <button
                          onClick={() => openGlossary('Strategy Stack')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Strategy Stack
                        </button>
                        <button
                          onClick={() => openGlossary('Advisor Integration')}
                          className="bg-navy-100 hover:bg-navy-200 text-navy-800 px-3 py-2 rounded-lg text-sm transition-colors duration-200"
                        >
                          📚 Advisor Integration
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              </div>
              
              {/* Video Player Placeholder */}
              <div className="bg-black h-64 md:h-96 flex items-center justify-center">
                <div className="text-white text-center">
                  <svg className="w-16 h-16 mx-auto mb-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                  </svg>
                  <p className="text-lg">Video Player</p>
                  <p className="text-sm text-gray-400">Duration: {lesson.duration_minutes} minutes</p>
                </div>
              </div>
              
              {/* Lesson Content */}
              <div className="p-6" onClick={handleContentClick}>
                <div className="prose max-w-none">
                  <div 
                    className="text-gray-700 leading-relaxed whitespace-pre-line"
                    dangerouslySetInnerHTML={{
                      __html: renderContentWithGlossary(lesson.content)
                    }}
                  />
                </div>
                
                {/* Quiz Section */}
                {!showQuiz && !showQuizResults && (
                  <div className="mt-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
                    <h3 className="text-xl font-bold text-navy-900 mb-4">Test Your Knowledge</h3>
                    <p className="text-gray-700 mb-4">Complete the quiz to earn XP and reinforce your learning.</p>
                    <button
                      onClick={startQuiz}
                      className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200"
                    >
                      Start Quiz ({lesson.xp_available || 150} XP Available)
                    </button>
                  </div>
                )}
                
                {/* Quiz Interface */}
                {showQuiz && !showQuizResults && quizQuestions.length > 0 && (
                  <div className="mt-8 p-6 bg-white border border-gray-200 rounded-lg">
                    <div className="mb-4">
                      <span className="text-sm text-gray-500">
                        Question {currentQuestion + 1} of {quizQuestions.length}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-navy-900 mb-6">
                      {quizQuestions[currentQuestion].question}
                    </h3>
                    <div className="space-y-3 mb-6">
                      {quizQuestions[currentQuestion].options.map((option, index) => (
                        <button
                          key={index}
                          onClick={() => setSelectedAnswer(option)}
                          className={`w-full text-left p-4 border-2 rounded-lg transition-colors duration-200 ${
                            selectedAnswer === option
                              ? 'border-emerald-500 bg-emerald-100'
                              : 'border-gray-200 hover:border-emerald-400 hover:bg-emerald-50'
                          }`}
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={submitAnswer}
                      disabled={!selectedAnswer}
                      className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                    >
                      Submit Answer
                    </button>
                  </div>
                )}
                
                {/* Quiz Results */}
                {showQuizResults && (
                  <div className="mt-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
                    <h3 className="text-xl font-bold text-navy-900 mb-4">Quiz Complete!</h3>
                    <div className="mb-4">
                      <span className="text-2xl font-bold text-emerald-600">
                        +{quizResults.filter(r => r.correct).reduce((total, result) => total + result.points, 0)} XP Earned
                      </span>
                    </div>
                    <div className="space-y-4">
                      {quizResults.map((result, index) => (
                        <div key={index} className="bg-white p-4 rounded-lg">
                          <p className="font-medium text-navy-900 mb-2">{result.question}</p>
                          <div className="flex items-center space-x-4">
                            <span className={`px-3 py-1 rounded-full text-sm ${
                              result.correct 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {result.correct ? '✅ Correct' : '❌ Incorrect'}
                            </span>
                            {!result.correct && (
                              <span className="text-gray-600 text-sm">
                                Correct: {result.correctAnswer}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-2">{result.explanation}</p>
                          {/* Add glossary links for quiz explanations */}
                          <div className="mt-2">
                            <button
                              onClick={() => setShowGlossary(false)}
                              className="text-emerald-600 hover:text-emerald-800 text-sm underline"
                            >
                              View Related Glossary Terms →
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Navigation */}
                <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
                  <button 
                    onClick={() => setCurrentLesson(Math.max(0, currentLesson - 1))}
                    disabled={currentLesson === 0}
                    className="flex items-center px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Previous
                  </button>
                  
                  <button 
                    onClick={() => setCurrentLesson(Math.min(course.lessons.length - 1, currentLesson + 1))}
                    disabled={currentLesson === course.lessons.length - 1}
                    className="flex items-center px-6 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                  >
                    Next
                    <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Sidebar */}
          <div className="lg:w-1/3">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-navy-900 mb-4">Course Lessons</h3>
              <div className="space-y-3">
                {course.lessons.map((lessonItem, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentLesson(index)}
                    className={`w-full text-left p-3 rounded-lg transition-colors duration-200 ${
                      index === currentLesson
                        ? 'bg-emerald-100 border-l-4 border-emerald-500'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium text-navy-900">{lessonItem.title}</div>
                    <div className="text-sm text-gray-600">{lessonItem.duration_minutes} minutes</div>
                    {course.type === 'w2' && (
                      <div className="flex items-center mt-2">
                        <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                          XP Available: {lessonItem.xp_available || 150}
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Glossary Modal */}
      {showGlossary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-navy-900">{showGlossary.term}</h3>
                  {!viewedGlossaryTerms.has(showGlossary.id) && (
                    <span className="text-sm text-emerald-600 font-semibold">+5 XP for viewing!</span>
                  )}
                </div>
                <button
                  onClick={() => setShowGlossary(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-gray-700 mb-4">{showGlossary.definition}</p>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                  {showGlossary.category}
                </span>
                {showGlossary.related_terms.map((term, index) => (
                  <button
                    key={index}
                    onClick={() => openGlossary(term)}
                    className="text-xs bg-navy-100 text-navy-700 px-2 py-1 rounded hover:bg-navy-200 transition-colors duration-200"
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Premium Tools Overview Component
const PremiumToolsSection = () => {
  const tools = [
    {
      name: "AI Strategy Assistant",
      subtitle: "TaxBot",
      icon: "🤖",
      description: "GPT-powered assistant trained on IRS Escape Plan modules, glossary, and client case studies. Ask personalized questions and get strategy breakdowns with citations.",
      features: ["Personalized tax guidance", "Module citations & links", "Strategy breakdowns", "24/7 availability"],
      gradient: "from-blue-500 to-blue-600"
    },
    {
      name: "Strategy Simulators", 
      subtitle: "Interactive Calculators",
      icon: "📊",
      description: "Five powerful calculators including Roth Conversion impact, REPS Hour Tracker, Cost Segregation ROI, W-2 Offset Planner, and Bonus Depreciation Forecast.",
      features: ["Downloadable summaries", "Tax impact estimates", "Real-time calculations", "Multiple scenarios"],
      gradient: "from-emerald-500 to-emerald-600"
    },
    {
      name: "Advisor Chat + Office Hours",
      subtitle: "Live Expert Support", 
      icon: "🧑‍💼",
      description: "Live Zoom Q&A sessions twice per week plus private in-app advisor messaging with 1 question per day limit for implementation support.",
      features: ["Live Zoom sessions 2x/week", "Private advisor messaging", "Implementation guidance", "Complex tax question support"],
      gradient: "from-purple-500 to-purple-600"
    },
    {
      name: "Playbook Generator",
      subtitle: "Custom Tax Blueprint",
      icon: "🛠️", 
      description: "Customized tax blueprint based on your income, real estate, investments, and goals. Links to relevant modules and adapts as laws change.",
      features: ["Custom tax blueprints", "Module integration", "Dynamic updates", "Goal-based planning"],
      gradient: "from-orange-500 to-orange-600"
    },
    {
      name: "Document Analyzer",
      subtitle: "AI Tax Form Analysis",
      icon: "📄",
      description: "Upload W-2, 1040, K-1, or entity returns for AI analysis. Detects missed deductions, audit risks, and eligible strategies with clear action plans.",
      features: ["Multi-format support", "Missed deduction detection", "Audit risk analysis", "Actionable recommendations"],
      gradient: "from-red-500 to-red-600"
    },
    {
      name: "Gamification + XP System",
      subtitle: "Progress Tracking",
      icon: "🎮",
      description: "Earn XP and badges by completing content, using tools, uploading documents, and community engagement. Includes leaderboard and milestone rewards.",
      features: ["XP & badge system", "Community leaderboard", "Milestone rewards", "1-on-1 strategy calls"],
      gradient: "from-pink-500 to-pink-600"
    },
    {
      name: "Mobile Dashboard",
      subtitle: "iOS & Android App",
      icon: "📱",
      description: "Mobile-first access to all tools, REPS logging on the go, push alerts for law changes, and personalized strategy reminders.",
      features: ["iOS & Android apps", "REPS activity logging", "Push notifications", "Strategy reminders"],
      gradient: "from-indigo-500 to-indigo-600"
    }
  ];

  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-navy-900 mb-4">
            Premium <span className="text-emerald-500">Tools Bundle</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-6">
            Advanced AI-powered tools and personalized features that unlock with your monthly subscription
          </p>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl mx-auto">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span className="text-red-700 font-bold text-sm">Subscription Required</span>
            </div>
            <p className="text-red-600 text-sm">
              These tools require an active monthly subscription to access. Course content remains available forever.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {tools.map((tool, index) => (
            <div key={index} className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden">
              <div className={`bg-gradient-to-r ${tool.gradient} p-6 text-white`}>
                <div className="flex items-center mb-3">
                  <span className="text-3xl mr-3">{tool.icon}</span>
                  <div>
                    <h3 className="text-xl font-bold">{tool.name}</h3>
                    <p className="text-sm opacity-90">{tool.subtitle}</p>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                  {tool.description}
                </p>
                
                <div className="space-y-2">
                  <h4 className="font-semibold text-navy-900 text-sm">Key Features:</h4>
                  <ul className="space-y-1">
                    {tool.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start text-sm text-gray-600">
                        <svg className="w-4 h-4 text-emerald-500 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Requires subscription</span>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 text-red-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-xs text-red-500 font-medium">Premium</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <div className="bg-navy-900 rounded-2xl p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold text-white mb-4">Ready to Unlock Premium Tools?</h3>
            <p className="text-gray-300 mb-6">
              Get instant access to all premium tools with any active subscription plan
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-gradient-to-r from-teal-500 to-teal-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all duration-200">
                Start W-2 Plan ($49/mo)
              </button>
              <button className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all duration-200">
                Start Business Plan ($49/mo)
              </button>
              <button className="bg-gradient-to-r from-pink-500 to-pink-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all duration-200">
                Get All Access ($69/mo)
              </button>
            </div>
            <p className="text-gray-400 text-sm mt-4">
              All plans require one-time course fee + monthly subscription • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

// Premium Tools Overview Component
const PremiumToolsOverview = () => {
  const tools = [
    {
      name: "AI Strategy Assistant",
      subtitle: "TaxBot",
      icon: "🤖",
      description: "GPT-powered assistant trained on IRS Escape Plan modules, glossary, and client case studies. Ask personalized questions and get strategy breakdowns with citations.",
      features: ["Personalized tax guidance", "Module citations & links", "Strategy breakdowns", "24/7 availability"],
      gradient: "from-blue-500 to-blue-600"
    },
    {
      name: "Strategy Simulators", 
      subtitle: "Interactive Calculators",
      icon: "📊",
      description: "Five powerful calculators including Roth Conversion impact, REPS Hour Tracker, Cost Segregation ROI, W-2 Offset Planner, and Bonus Depreciation Forecast.",
      features: ["Downloadable summaries", "Tax impact estimates", "Real-time calculations", "Multiple scenarios"],
      gradient: "from-emerald-500 to-emerald-600"
    },
    {
      name: "Advisor Chat + Office Hours",
      subtitle: "Live Expert Support", 
      icon: "🧑‍💼",
      description: "Live Zoom Q&A sessions twice per week plus private in-app advisor messaging with 1 question per day limit for implementation support.",
      features: ["Live Zoom sessions 2x/week", "Private advisor messaging", "Implementation guidance", "Complex tax question support"],
      gradient: "from-purple-500 to-purple-600"
    },
    {
      name: "Playbook Generator",
      subtitle: "Custom Tax Blueprint",
      icon: "🛠️", 
      description: "Customized tax blueprint based on your income, real estate, investments, and goals. Links to relevant modules and adapts as laws change.",
      features: ["Custom tax blueprints", "Module integration", "Dynamic updates", "Goal-based planning"],
      gradient: "from-orange-500 to-orange-600"
    },
    {
      name: "Document Analyzer",
      subtitle: "AI Tax Form Analysis",
      icon: "📄",
      description: "Upload W-2, 1040, K-1, or entity returns for AI analysis. Detects missed deductions, audit risks, and eligible strategies with clear action plans.",
      features: ["Multi-format support", "Missed deduction detection", "Audit risk analysis", "Actionable recommendations"],
      gradient: "from-red-500 to-red-600"
    },
    {
      name: "Gamification + XP System",
      subtitle: "Progress Tracking",
      icon: "🎮",
      description: "Earn XP and badges by completing content, using tools, uploading documents, and community engagement. Includes leaderboard and milestone rewards.",
      features: ["XP & badge system", "Community leaderboard", "Milestone rewards", "1-on-1 strategy calls"],
      gradient: "from-pink-500 to-pink-600"
    },
    {
      name: "Mobile Dashboard",
      subtitle: "iOS & Android App",
      icon: "📱",
      description: "Mobile-first access to all tools, REPS logging on the go, push alerts for law changes, and personalized strategy reminders.",
      features: ["iOS & Android apps", "REPS activity logging", "Push notifications", "Strategy reminders"],
      gradient: "from-indigo-500 to-indigo-600"
    }
  ];

  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-navy-900 mb-4">
            Premium <span className="text-emerald-500">Tools Bundle</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-6">
            Advanced AI-powered tools and personalized features that unlock with your monthly subscription
          </p>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl mx-auto">
            <div className="flex items-center justify-center mb-2">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span className="text-red-700 font-bold text-sm">Subscription Required</span>
            </div>
            <p className="text-red-600 text-sm">
              These tools require an active monthly subscription to access. Course content remains available forever.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {tools.map((tool, index) => (
            <div key={index} className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden">
              <div className={`bg-gradient-to-r ${tool.gradient} p-6 text-white`}>
                <div className="flex items-center mb-3">
                  <span className="text-3xl mr-3">{tool.icon}</span>
                  <div>
                    <h3 className="text-xl font-bold">{tool.name}</h3>
                    <p className="text-sm opacity-90">{tool.subtitle}</p>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                  {tool.description}
                </p>
                
                <div className="space-y-2">
                  <h4 className="font-semibold text-navy-900 text-sm">Key Features:</h4>
                  <ul className="space-y-1">
                    {tool.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start text-sm text-gray-600">
                        <svg className="w-4 h-4 text-emerald-500 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Requires subscription</span>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 text-red-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-xs text-red-500 font-medium">Premium</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <div className="bg-navy-900 rounded-2xl p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold text-white mb-4">Ready to Unlock Premium Tools?</h3>
            <p className="text-gray-300 mb-6">
              Get instant access to all premium tools with any active subscription plan
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-gradient-to-r from-teal-500 to-teal-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all duration-200">
                Start W-2 Plan ($49/mo)
              </button>
              <button className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all duration-200">
                Start Business Plan ($49/mo)
              </button>
              <button className="bg-gradient-to-r from-pink-500 to-pink-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all duration-200">
                Get All Access ($69/mo)
              </button>
            </div>
            <p className="text-gray-400 text-sm mt-4">
              All plans require one-time course fee + monthly subscription • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

// Tools Section Component
const ToolsSection = ({ tools }) => {
  return (
    <div className="py-12">
      <div className="container mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy-900 mb-8 text-center">Tax Tools & Calculators</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map((tool) => (
            <div key={tool.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
              <div className="flex items-center mb-4">
                <div className="bg-emerald-100 p-3 rounded-lg mr-4">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-900">{tool.name}</h3>
                  {tool.is_free ? (
                    <span className="text-emerald-600 text-sm font-semibold">FREE</span>
                  ) : (
                    <span className="text-amber-600 text-sm font-semibold">PREMIUM</span>
                  )}
                </div>
              </div>
              <p className="text-gray-600 mb-4">{tool.description}</p>
              <button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-2 rounded-lg transition-colors duration-200">
                {tool.is_free ? 'Use Tool' : 'Upgrade to Access'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Glossary Section Component
const GlossarySection = ({ glossaryTerms }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTerms, setFilteredTerms] = useState(glossaryTerms);
  
  useEffect(() => {
    if (searchTerm) {
      const filtered = glossaryTerms.filter(term =>
        term.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
        term.definition.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredTerms(filtered);
    } else {
      setFilteredTerms(glossaryTerms);
    }
  }, [searchTerm, glossaryTerms]);
  
  return (
    <div className="py-12">
      <div className="container mx-auto px-6">
        <h2 className="text-3xl font-bold text-navy-900 mb-8 text-center">Tax Glossary</h2>
        
        <div className="max-w-2xl mx-auto mb-8">
          <div className="relative">
            <input
              type="text"
              placeholder="Search tax terms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <svg className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {filteredTerms.map((term) => (
            <div key={term.id} className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-navy-900 mb-2">{term.term}</h3>
              <p className="text-gray-600 mb-4">{term.definition}</p>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                  {term.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Marketplace Section Component
const MarketplaceSection = () => {
  return (
    <div className="py-12">
      <div className="container mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold text-navy-900 mb-8">Marketplace</h2>
        <div className="bg-white rounded-lg shadow-lg p-12 max-w-2xl mx-auto">
          <div className="mb-6">
            <svg className="w-16 h-16 mx-auto text-emerald-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m4 0V9a2 2 0 012-2h2a2 2 0 012 2v12M13 7h.01M9 7h.01" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-navy-900 mb-4">Coming Soon</h3>
          <p className="text-gray-600 mb-6">
            The marketplace will feature additional premium courses, one-on-one consultations, 
            and specialized tax tools from certified professionals.
          </p>
          <button className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-lg transition-colors duration-200">
            Notify Me When Available
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [activeSection, setActiveSection] = useState('courses');
  const [courses, setCourses] = useState([]);
  const [tools, setTools] = useState([]);
  const [glossaryTerms, setGlossaryTerms] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchData();
  }, []);
  
  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch courses
      const coursesResponse = await fetch(`${API_BASE_URL}/api/courses`);
      const coursesData = await coursesResponse.json();
      setCourses(coursesData);
      
      // Fetch tools
      const toolsResponse = await fetch(`${API_BASE_URL}/api/tools`);
      const toolsData = await toolsResponse.json();
      setTools(toolsData);
      
      // Fetch glossary
      const glossaryResponse = await fetch(`${API_BASE_URL}/api/glossary`);
      const glossaryData = await glossaryResponse.json();
      setGlossaryTerms(glossaryData);
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleCourseClick = (course) => {
    setSelectedCourse(course);
  };
  
  const handleBackToCourses = () => {
    setSelectedCourse(null);
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-emerald-400 mx-auto mb-4"></div>
          <p className="text-white text-xl">Loading IRS Escape Plan...</p>
        </div>
      </div>
    );
  }
  
  if (selectedCourse) {
    return <CourseViewer course={selectedCourse} onBack={handleBackToCourses} />;
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeSection={activeSection} setActiveSection={setActiveSection} />
      
      {activeSection === 'courses' && (
        <>
          <HeroSection />
          <PricingSection />
          <section className="py-12">
            <div className="container mx-auto px-6">
              <h2 className="text-3xl font-bold text-navy-900 mb-8 text-center">Choose Your Path</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {courses.map((course) => (
                  <CourseCard 
                    key={course.id} 
                    course={course} 
                    onCourseClick={handleCourseClick}
                  />
                ))}
              </div>
            </div>
          </section>
        </>
      )}
      {activeSection === 'taxbot' && <TaxBotSection />}
      {activeSection === 'premium-tools' && <PremiumToolsOverview />}
      
      {activeSection === 'tools' && <ToolsSection tools={tools} />}
      {activeSection === 'glossary' && <GlossarySection glossaryTerms={glossaryTerms} />}
      {activeSection === 'marketplace' && <MarketplaceSection />}
    </div>
  );
};

// Premium Pricing Section Component
const PricingSection = () => {
  const plans = [
    {
      name: "W-2 Escape Plan",
      accent: "teal",
      oneTimePrice: "$997",
      oneTimeDescription: "one-time course fee",
      monthlyPrice: "$49/mo",
      monthlyDescription: "platform subscription",
      description: "High-income W-2 earners unlock deduction stacking, REPS access, and repositioning strategies.",
      features: [
        "Lifetime access to W-2 course modules",
        "AI Strategy Assistant (TaxBot) for W-2 questions", 
        "W-2 Offset Planner & REPS Hour Tracker",
        "Document Analyzer for W-2 & 1040 optimization",
        "Gamification + XP tracking system",
        "Mobile dashboard with strategy reminders"
      ],
      ctaText: "Start W-2 Plan",
      gradient: "from-teal-500 to-teal-600",
      border: "border-teal-200",
      bg: "bg-teal-50"
    },
    {
      name: "Business Owner Plan", 
      accent: "yellow",
      oneTimePrice: "$1,497",
      oneTimeDescription: "one-time course fee",
      monthlyPrice: "$49/mo",
      monthlyDescription: "platform subscription",
      description: "Entity optimization, MSO design, QBI qualification, and asset-backed exit strategies.",
      features: [
        "Lifetime access to Business Owner course",
        "AI Strategy Assistant (TaxBot) for entity questions",
        "Cost Segregation ROI & Bonus Depreciation tools",
        "Playbook Generator for business structures",
        "Document Analyzer for K-1 & entity returns",
        "Weekly office hours + advisor chat support"
      ],
      ctaText: "Start Business Plan",
      gradient: "from-yellow-500 to-yellow-600", 
      border: "border-yellow-200",
      bg: "bg-yellow-50"
    },
    {
      name: "All Access + AI",
      accent: "pink", 
      oneTimePrice: "$1,994",
      oneTimeDescription: "one-time course bundle",
      monthlyPrice: "$69/mo",
      monthlyDescription: "premium subscription",
      description: "Complete access to both courses, all tools, XP tracking, and your personal AI tax strategist.",
      features: [
        "Lifetime access to ALL courses & content",
        "Full AI Strategy Assistant (TaxBot) - unlimited access", 
        "Complete strategy simulator suite (Roth, REPS, W-2)",
        "Advanced Playbook Generator with custom blueprints",
        "Premium Document Analyzer for all tax forms",
        "Mobile app + priority advisor chat + office hours"
      ],
      ctaText: "Get All Access",
      gradient: "from-pink-500 to-pink-600",
      border: "border-pink-200", 
      bg: "bg-pink-50",
      popular: true,
      savings: "Save $500"
    }
  ];

  return (
    <section className="py-16 bg-navy-900">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">
            Choose Your <span className="text-emerald-400">Tax Freedom</span> Plan
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-6">
            Professional tax strategies used by high-income earners to minimize tax burden and build wealth
          </p>
          <div className="bg-emerald-900/50 border border-emerald-400/30 rounded-lg p-4 max-w-2xl mx-auto">
            <p className="text-emerald-300 text-sm">
              <strong>Full Platform Access Requires:</strong> One-time course fee + Active monthly subscription
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div key={index} className={`relative bg-white rounded-2xl shadow-xl overflow-hidden transform hover:scale-105 transition-all duration-300 ${plan.popular ? 'ring-4 ring-emerald-400' : ''}`}>
              {plan.popular && (
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <span className="bg-emerald-400 text-navy-900 px-4 py-1 rounded-full text-sm font-bold">
                    MOST POPULAR
                  </span>
                </div>
              )}
              
              {plan.savings && (
                <div className="absolute top-4 right-4">
                  <span className="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold">
                    {plan.savings}
                  </span>
                </div>
              )}
              
              <div className={`${plan.bg} px-6 py-8 border-b ${plan.border}`}>
                <h3 className="text-2xl font-bold text-navy-900 mb-2">{plan.name}</h3>
                <p className="text-gray-600 text-sm mb-6">{plan.description}</p>
                
                <div className="space-y-3">
                  <div className="bg-white rounded-lg p-3 border-2 border-gray-200">
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold text-navy-900">{plan.oneTimePrice}</span>
                      <span className="text-gray-500 text-sm">{plan.oneTimeDescription}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">Lifetime course access</p>
                  </div>
                  
                  <div className="text-center text-gray-500 font-bold">+</div>
                  
                  <div className={`bg-white rounded-lg p-3 border-2 ${plan.accent === 'pink' ? 'border-pink-200' : 'border-navy-200'}`}>
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold text-navy-900">{plan.monthlyPrice}</span>
                      <span className="text-gray-500 text-sm">{plan.monthlyDescription}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {plan.accent === 'pink' ? 'Premium AI tools & features' : 'AI tools & platform features'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="px-6 py-6">
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <svg className="w-5 h-5 text-emerald-500 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-700 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <button className={`w-full bg-gradient-to-r ${plan.gradient} text-white py-4 px-6 rounded-xl font-bold text-lg hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200`}>
                  {plan.ctaText}
                </button>
                
                <p className="text-xs text-gray-500 text-center mt-3">
                  Cancel anytime • Keep course access forever
                </p>
              </div>
            </div>
          ))}
        </div>
        
        <div className="max-w-4xl mx-auto mt-12">
          <div className="bg-navy-800 border border-navy-600 rounded-xl p-6">
            <h3 className="text-white text-lg font-bold mb-4 text-center">What You Get With Your Investment</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-navy-700 rounded-lg p-4">
                <h4 className="text-emerald-400 font-bold mb-2">One-Time Course Fee Includes:</h4>
                <ul className="text-gray-300 text-sm space-y-1">
                  <li>• Lifetime access to course modules</li>
                  <li>• Downloadable resources & worksheets</li>
                  <li>• Case studies & implementation guides</li>
                  <li>• Static course content forever</li>
                </ul>
              </div>
              <div className="bg-navy-700 rounded-lg p-4">
                <h4 className="text-emerald-400 font-bold mb-2">Monthly Subscription Unlocks:</h4>
                <ul className="text-gray-300 text-sm space-y-1">
                  <li>• AI Strategy Assistant (TaxBot) - personalized guidance</li>
                  <li>• Strategy simulators (Roth, REPS, W-2 offset, etc.)</li>
                  <li>• Playbook Generator with custom tax blueprints</li>
                  <li>• Document Analyzer for tax form optimization</li>
                  <li>• Weekly office hours + in-app advisor chat</li>
                  <li>• Mobile app with push alerts & progress tracking</li>
                </ul>
              </div>
            </div>
            
            <div className="mt-6 bg-navy-600 rounded-lg p-4">
              <div className="flex items-center justify-center mb-2">
                <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="text-red-400 font-bold text-sm">Important:</span>
              </div>
              <p className="text-gray-300 text-sm text-center">
                <strong>Full platform functionality requires both payments.</strong> Canceling your subscription means you keep lifetime course access but lose AI features, tools, and premium support.
              </p>
            </div>
          </div>
        </div>
        
        <div className="text-center mt-8">
          <p className="text-gray-400 text-sm mb-4">
            30-day money-back guarantee on course fee • Cancel subscription anytime • Secure payment
          </p>
          <div className="flex items-center justify-center space-x-6 text-gray-500">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
              Secure SSL
            </div>
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Course Access Forever
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default App;