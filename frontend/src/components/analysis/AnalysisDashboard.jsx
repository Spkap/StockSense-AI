import React, { useState, useEffect } from 'react';

const AnalysisDashboard = ({ stock, onClose, analysisData, loading }) => {
  const [modalKey, setModalKey] = useState(0);
  console.log('AnalysisDashboard props - stock:', stock, 'loading:', loading, 'analysisData:', analysisData);
  if (!stock) return null;
  
  if (loading) {
    console.log('Rendering loading state for AnalysisDashboard');
    return (
      <div 
        className="fixed inset-0 z-[99999] flex items-center justify-center p-4"
        onClick={(e) => e.stopPropagation()}
        style={{ 
          zIndex: 99999,
          backdropFilter: 'blur(10px)',
          background: 'rgba(0, 0, 0, 0.7)'
        }}
      >
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-slate-600 shadow-2xl max-w-lg w-full p-8">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                {stock?.symbol}
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">AI Stock Analysis</h3>
                <p className="text-slate-400 text-sm">Analysis in Progress</p>
              </div>
            </div>
            <button 
              className="text-slate-400 hover:text-white transition-colors p-2 rounded-full hover:bg-slate-700" 
              onClick={onClose}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Loading Animation */}
          <div className="text-center py-12">
            <div className="relative mb-8">
              <div className="w-20 h-20 rounded-full border-4 border-slate-600 border-t-blue-500 animate-spin mx-auto"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-12 h-12 bg-blue-500 rounded-full animate-pulse"></div>
              </div>
            </div>
            
            {/* Progress Indicator */}
            <div className="mb-6">
              <div className="flex justify-center mb-3">
                <span className="text-blue-400 text-sm font-medium">GATHERING NEWS SENTIMENT</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-pink-500 to-blue-500 h-2 rounded-full animate-pulse" style={{width: '70%'}}></div>
              </div>
            </div>
            
            {/* Status Steps */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-green-400">Market Data Collected</span>
                </div>
                <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-green-400">News Analysis Complete</span>
                </div>
                <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-blue-400">Processing AI Analysis</span>
                </div>
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            </div>
            
            <div className="mt-8">
              <p className="text-white font-semibold mb-1">
                Analyzing {stock?.symbol}...
              </p>
              <p className="text-slate-400 text-sm">
                Generating comprehensive market insights
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  useEffect(() => {
    // Force remount when new data arrives
    if (analysisData) {
      setModalKey(prev => prev + 1);
    }
  }, [analysisData]);

  if (!analysisData || !analysisData.analysis) {
    // If not loading and no data, show error state
    if (!loading) {
      return (
        <div 
          className="fixed inset-0 z-[99999] flex items-center justify-center p-4"
          onClick={(e) => e.stopPropagation()}
          style={{ 
            zIndex: 99999,
            backdropFilter: 'blur(10px)',
            background: 'rgba(0, 0, 0, 0.7)'
          }}
        >
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-slate-600 shadow-2xl max-w-lg w-full p-8">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-3">
                <div className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                  {stock?.symbol}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Analysis Failed</h3>
                  <p className="text-slate-400 text-sm">Unable to complete analysis</p>
                </div>
              </div>
              <button 
                className="text-slate-400 hover:text-white transition-colors p-2 rounded-full hover:bg-slate-700" 
                onClick={onClose}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L5.232 15.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <p className="text-white font-semibold mb-2 text-lg">
                Unable to analyze {stock?.symbol}
              </p>
              <p className="text-slate-400 text-sm mb-6">
                Please check your connection and try again
              </p>
              <button 
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors" 
                onClick={onClose}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-[99999]"
        onClick={(e) => e.stopPropagation()}
        style={{ zIndex: 99999 }}
      >
        <div className="modal-box bg-black border border-white">
          <div className="text-center">
            <span className="loading loading-spinner loading-lg text-primary"></span>
            <p className="text-white mt-4">Loading analysis data...</p>
          </div>
        </div>
      </div>
    );
  }

  const formatSummaryText = (text) => {
    if (!text || typeof text !== 'string') {
      return 'No analysis summary available';
    }

    // Split into paragraphs
    let paragraphs = text.split('\n\n').filter(p => p.trim());
    
    // Remove unwanted sections
    paragraphs = paragraphs.filter(paragraph => {
      const lowerParagraph = paragraph.toLowerCase();
      // Remove analysis completion messages
      if (lowerParagraph.includes('analysis completed using') || 
          lowerParagraph.includes('tools across') ||
          lowerParagraph.includes('reasoning iterations')) {
        return false;
      }
      return true;
    });
    
    let finalRecommendationFound = false;
    paragraphs = paragraphs.filter(paragraph => {
      const isRecommendation = paragraph.toLowerCase().includes('final recommendation') || 
                              paragraph.toLowerCase().includes('recommendation:');
      
      if (isRecommendation) {
        if (finalRecommendationFound) {
          return false; // Skip duplicate recommendations
        }
        finalRecommendationFound = true;
      }
      return true;
    });

    // Enhanced formatting with structure detection
    paragraphs = paragraphs.map(paragraph => {
      // Remove excessive line breaks
      let cleaned = paragraph.replace(/\n{3,}/g, '\n\n').trim();
      
      // Preserve markdown formatting for better styling
      cleaned = cleaned
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic text
        .replace(/#{1,6}\s(.+)/g, '<h4 class="summary-heading">$1</h4>') // Headers
        .replace(/^\d+\.\s/gm, '') // Remove numbered list markers
        .replace(/^[-•]\s/gm, '• '); // Standardize bullet points
      
      return cleaned;
    }).filter(paragraph => {
      // Remove empty or nearly empty paragraphs
      const textContent = paragraph.replace(/<[^>]*>/g, '').trim();
      return textContent.length > 5; // Only keep paragraphs with meaningful content
    });

    return paragraphs;
  };

  // Helper function to clean markdown formatting from text
  const cleanMarkdownText = (text) => {
    if (!text || typeof text !== 'string') return text;
    
    return text
      .replace(/\*\*/g, '') // Remove bold markers
      .replace(/\*/g, '')   // Remove italic markers
      .replace(/#{1,6}\s/g, '') // Remove heading markers
      .replace(/`{1,3}/g, '') // Remove code markers
      .trim();
  };

  const renderSentimentContent = (content) => {
    if (!content) return null;
    
    // Handle case where content is an object with a "content" property
    let textContent = content;
    if (typeof content === 'object') {
      if (content.content) {
        textContent = content.content;
      } else {
        // If it's a complex object, try to extract meaningful text
        try {
          textContent = JSON.stringify(content, null, 2);
        } catch (e) {
          return (
            <div className="sentiment-error">
              <p>Error: Unable to display sentiment content - invalid data type</p>
            </div>
          );
        }
      }
    }
    
    // Ensure content is a string
    if (typeof textContent !== 'string') {
      textContent = String(textContent || '');
    }

    // Split content into sections and format accordingly
    const sections = textContent.split('\n\n');
    
    return (
      <div className="sentiment-analysis-content">
        {sections.map((section, index) => {
          // Skip empty sections
          if (!section.trim()) return null;
          
          // Handle headlines with bullet points and sentiment analysis
          if (section.includes('Headline:') || section.includes('* Sentiment:')) {
            return (
              <div key={index} className="headline-analysis-block">
                {section.split('\n').map((line, lineIndex) => {
                  if (line.trim().startsWith('Headline:')) {
                    return (
                      <div key={lineIndex} className="headline-text">
                        {cleanMarkdownText(line.replace('Headline:', ''))}
                      </div>
                    );
                  } else if (line.trim().startsWith('* Sentiment:')) {
                    const sentiment = line.replace('* Sentiment:', '').trim();
                    const sentimentClass = sentiment.toLowerCase().includes('positive') ? 'positive' :
                                         sentiment.toLowerCase().includes('negative') ? 'negative' : 'neutral';
                    return (
                      <div key={lineIndex} className={`sentiment-badge ${sentimentClass}`}>
                        <span className="sentiment-icon">
                          {sentimentClass === 'positive' ? '+' : sentimentClass === 'negative' ? '-' : '~'}
                        </span>
                        Sentiment: {sentiment}
                      </div>
                    );
                  } else if (line.trim().startsWith('* Justification:')) {
                    return (
                      <div key={lineIndex} className="justification-text">
                        {cleanMarkdownText(line.replace('* Justification:', '').trim())}
                      </div>
                    );
                  } else if (line.trim()) {
                    // Remove numbering and bullet points from the line
                    const cleanLine = line.replace(/^\d+\.\s*/, '').replace(/^[•\-*]\s*/, '').trim();
                    if (cleanLine) {
                      return (
                        <div key={lineIndex} style={{ color: '#e5e7eb', marginBottom: '0.25rem' }}>
                          {cleanMarkdownText(cleanLine)}
                        </div>
                      );
                    }
                  }
                  return null;
                })}
              </div>
            );
          }
          
          // Handle section headers (like "Overall Market Sentiment Summary:")
          if (section.includes(':') && section.split('\n')[0].endsWith(':')) {
            const lines = section.split('\n');
            const header = lines[0];
            const content = lines.slice(1).join('\n');
            
            return (
              <div key={index} className="sentiment-summary-section" style={{
                marginBottom: '1.5rem'
              }}>
                <h4 style={{ 
                  color: '#a78bfa', 
                  borderBottom: '2px solid rgba(167, 139, 250, 0.3)',
                  paddingBottom: '0.5rem',
                  marginBottom: '1rem',
                  fontSize: '1.1rem'
                }}>
                  {header.replace(':', '')}
                </h4>
                <div style={{ 
                  color: '#e5e7eb', 
                  lineHeight: '1.6',
                  paddingLeft: '1rem'
                }}>
                  {content.split('\n').map((line, lineIdx) => {
                    if (!line.trim()) return null;
                    if (line.startsWith('*')) {
                      // Remove bullet points and numbering
                      const cleanLine = line.replace(/^\*\s*/, '').replace(/^\d+\.\s*/, '').replace(/^[•\-*]\s*/, '').trim();
                      return (
                        <div key={lineIdx} style={{ 
                          marginBottom: '0.75rem',
                          paddingLeft: '1rem',
                          borderLeft: '3px solid rgba(167, 139, 250, 0.5)'
                        }}>
                          {cleanMarkdownText(cleanLine)}
                        </div>
                      );
                    }
                    return (
                      <p key={lineIdx} style={{ marginBottom: '0.75rem' }}>
                        {cleanMarkdownText(line)}
                      </p>
                    );
                  })}
                </div>
              </div>
            );
          }
          
          // Handle list items with bullets
          if (section.includes('•') || section.match(/^\d+\./)) {
            const items = section.split('\n').filter(item => item.trim());
            return (
              <div key={index} className="sentiment-list" style={{
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '1rem'
              }}>
                {items.map((item, itemIndex) => {
                  // Remove numbering and bullet points from each item
                  const cleanItem = item.replace(/^\d+\.\s*/, '').replace(/^[•\-*]\s*/, '').trim();
                  return (
                    <div key={itemIndex} className="sentiment-list-item" style={{
                      marginBottom: '0.5rem',
                      color: '#e5e7eb',
                      lineHeight: '1.5'
                    }}>
                      {cleanMarkdownText(cleanItem)}
                    </div>
                  );
                })}
              </div>
            );
          }
          
          // Handle regular paragraphs
          if (section.trim()) {
            return (
              <div key={index} className="sentiment-paragraph" style={{
                color: '#e5e7eb',
                lineHeight: '1.6',
                marginBottom: '1rem'
              }}>
                {cleanMarkdownText(section)}
              </div>
            );
          }
          
          return null;
        }).filter(Boolean)}
      </div>
    );
  };

  return (
    <div 
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4"
      onClick={(e) => e.stopPropagation()}
      style={{ 
        zIndex: 99999,
        backdropFilter: 'blur(10px)',
        background: 'rgba(0, 0, 0, 0.7)'
      }}
    >
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-slate-600 shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header - Always at top */}

        {/* Scrollable Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="p-6 space-y-6">
          {/* Investment Verdict Card */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-xl border border-slate-600 shadow-lg">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">Investment Verdict</h3>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                <div className={`px-6 py-3 rounded-lg font-bold text-lg ${
                  (analysisData?.analysis?.recommendation || 'analyzing').toLowerCase() === 'buy' ? 'bg-green-600 text-white' :
                  (analysisData?.analysis?.recommendation || 'analyzing').toLowerCase() === 'sell' ? 'bg-red-600 text-white' :
                  (analysisData?.analysis?.recommendation || 'analyzing').toLowerCase() === 'hold' ? 'bg-yellow-600 text-white' :
                  'bg-slate-600 text-white'
                }`}>
                  {analysisData?.analysis?.recommendation || 'ANALYZING'}
                </div>
                {analysisData?.analysis?.confidence && (
                  <div className="flex items-center gap-3">
                    <span className="text-slate-400 text-sm">Confidence:</span>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      analysisData.analysis.confidence.toLowerCase() === 'high' ? 'bg-green-100 text-green-800' :
                      analysisData.analysis.confidence.toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {analysisData.analysis.confidence.toUpperCase()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Analysis Summary Card - Moved to top */}
          {analysisData?.analysis?.summary && (
            <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-xl border border-slate-600 shadow-lg">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white">AI Analysis Summary</h3>
                </div>
                <div className="text-slate-200 leading-relaxed">
                  {(() => {
                    const formattedSummary = formatSummaryText(analysisData.analysis.summary);
                    return Array.isArray(formattedSummary) 
                      ? formattedSummary.map((paragraph, index) => (
                          <div key={index} className="mb-4" dangerouslySetInnerHTML={{ __html: paragraph }} />
                        ))
                      : <p>{formattedSummary}</p>;
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* Market Sentiment Card */}
          {analysisData?.analysis?.sentiment_report && (
            <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-xl border border-slate-600 shadow-lg">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                      <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white">Market Sentiment</h3>
                </div>
                <div className="text-slate-200 leading-relaxed">
                  {renderSentimentContent(analysisData.analysis.sentiment_report)}
                </div>
              </div>
            </div>
          )}

          {/* Recent Headlines Card */}
          {analysisData?.data_sources?.news_headlines?.headlines && (
            <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-xl border border-slate-600 shadow-lg">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-orange-600 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M2 5a2 2 0 012-2h8a2 2 0 012 2v10a2 2 0 002 2H4a2 2 0 01-2-2V5zm3 1h6v4H5V6zm6 6H5v2h6v-2z" clipRule="evenodd" />
                      <path d="M15 7h1a2 2 0 012 2v5.5a1.5 1.5 0 01-3 0V7z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white">Recent News Headlines</h3>
                </div>
                <div className="space-y-4">
                  {(() => {
                    try {
                      const headlines = analysisData.data_sources.news_headlines.headlines;
                      if (!Array.isArray(headlines)) return null;
                      
                      return headlines.slice(0, 4).map((headline, index) => (
                        <div key={index} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                          <div className="text-slate-200 mb-2">
                            {headline?.headline || headline}
                          </div>
                          {headline?.url && (
                            <a 
                              href={headline.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
                            >
                              Read More →
                            </a>
                          )}
                        </div>
                      ));
                    } catch (error) {
                      return <div className="text-red-400">Error loading headlines</div>;
                    }
                  })()}
                </div>
              </div>
            </div>
          )}
          
          {/* Footer Actions */}
          <div className="flex justify-center pt-6">
            <button 
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors flex items-center gap-2" 
              onClick={onClose}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Dashboard
            </button>
          </div>
          
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisDashboard;