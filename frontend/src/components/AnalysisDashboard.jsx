import React, { useState, useEffect } from 'react';

const AnalysisDashboard = ({ stock, onClose, analysisData, loading }) => {
  const [modalKey, setModalKey] = useState(0);
  const [loadingStep, setLoadingStep] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);
  
  const loadingSteps = [
    { icon: '', text: 'Initializing AI analysis' },
    { icon: '', text: 'Collecting market data' },
    { icon: '', text: 'Gathering news sentiment' },
    { icon: '', text: 'AI processing' },
    { icon: '', text: 'Generating insights' },
    { icon: '', text: 'Finalizing report' }
  ];

  useEffect(() => {
    if (loading) {
      setLoadingStep(0);
      setLoadingProgress(0);
      
      const stepInterval = setInterval(() => {
        setLoadingStep(prev => {
          if (prev < loadingSteps.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 2000); // Change step every 2 seconds

      const progressInterval = setInterval(() => {
        setLoadingProgress(prev => {
          if (prev < 95) {
            return prev + Math.random() * 3; // Random progress increment
          }
          return prev;
        });
      }, 100);

      return () => {
        clearInterval(stepInterval);
        clearInterval(progressInterval);
      };
    }
  }, [loading]);

  // Don't render anything if no stock is being analyzed
  if (!stock) return null;
  
  if (loading) {
    return (
      <div className="modal-overlay" style={{ zIndex: 9999 }}>
        <div className="modal-content analysis-modal loading-modal">
          <div className="modal-header loading-header">
            <div className="loading-title-section">
              <div className="stock-symbol-badge">{stock?.symbol}</div>
              <h3>AI Stock Analysis in Progress</h3>
            </div>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          
          <div className="analysis-loading">
            <div className="loading-animation-container">
              <div className="ai-brain-animation">
                <div className="brain-core"></div>
                <div className="neural-network">
                  <div className="neural-pulse pulse-1"></div>
                  <div className="neural-pulse pulse-2"></div>
                  <div className="neural-pulse pulse-3"></div>
                  <div className="neural-pulse pulse-4"></div>
                </div>
              </div>
              
              <div className="loading-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${Math.min(loadingProgress, 95)}%` }}
                  ></div>
                </div>
                <div className="progress-percentage">
                  {loadingSteps[loadingStep]?.text || 'Analyzing...'}
                </div>
              </div>
            </div>
            
            <div className="loading-steps">
              {loadingSteps.map((step, index) => (
                <div key={index} className={`step-item ${
                  index < loadingStep ? 'completed' : 
                  index === loadingStep ? 'active' : 
                  index === loadingStep + 1 ? 'processing' : 'pending'
                }`}>
                  <div className="step-icon">{step.icon}</div>
                  <div className="step-content">
                    <span className="step-text">{step.text}</span>
                  </div>
                  {index < loadingStep && <div className="step-checkmark">✓</div>}
                </div>
              ))}
            </div>
            
            <div className="loading-messages">
              <p className="primary-message">
                {loadingSteps[loadingStep]?.text || 'Analyzing'} {stock?.symbol}
              </p>
              <p className="secondary-message">
                Processing comprehensive market analysis
              </p>
              <div className="progress-details">
                <span>Progress: {Math.round(loadingProgress)}%</span>
                <span>•</span>
                <span>Step {loadingStep + 1} of {loadingSteps.length}</span>
                <span>•</span>
                <span>ETA: {Math.max(10 - Math.floor(loadingProgress / 10), 1)}s</span>
              </div>
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
    return (
      <div className="modal-overlay">
        <div className="analysis-modal">
          <div className="error-container">
            <p>Loading analysis data...</p>
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
    
    // Remove duplicate "Final Recommendation" sections
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
    <div className="modal-overlay">
      <div className="analysis-dashboard-modal">
        {/* Header */}
        <div className="analysis-dashboard-header">
          <div className="stock-info-header">
            <div className="stock-symbol-large">
              {analysisData?.analysis?.symbol || stock?.symbol}
            </div>
            <div className="stock-details">
              <h2 className="stock-name">
                {analysisData?.analysis?.company_name || stock?.name || 'Stock Analysis'}
              </h2>
              <div className="analysis-timestamp">
                AI Analysis • {new Date().toLocaleString()}
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Main Content */}
        <div className="analysis-dashboard-content">
          {/* Investment Verdict Card */}
          <div className="analysis-card primary-card">
            <div className="card-header">
              
              <h3>Investment Verdict</h3>
            </div>
            <div className="verdict-display">
              <div className="verdict-main">
                <div className={`verdict-badge ${(analysisData?.analysis?.recommendation || 'analyzing').toLowerCase()}`}>
                  {analysisData?.analysis?.recommendation || 'ANALYZING'}
                </div>
                {analysisData?.analysis?.confidence && (
                  <div className="confidence-indicator">
                    <span className="confidence-text">
                      Confidence: <span className={`confidence-level ${analysisData.analysis.confidence.toLowerCase()}`}>
                        {analysisData.analysis.confidence.toUpperCase()}
                      </span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Market Sentiment Card */}
          {analysisData?.analysis?.sentiment_report && (
            <div className="analysis-card sentiment-card full-width-card">
              <div className="card-header">
                <div className="card-icon"></div>
                <h3>Market Sentiment</h3>
              </div>
              <div className="sentiment-display">
                {renderSentimentContent(analysisData.analysis.sentiment_report)}
              </div>
            </div>
          )}

          {/* Recent Headlines Card */}
          {analysisData?.data_sources?.news_headlines?.headlines && (
            <div className="analysis-card news-card full-width-card">
              <div className="card-header">
                <div className="card-icon"></div>
                <h3>Recent News Headlines</h3>
              </div>
              <div className="news-display">
                {(() => {
                  try {
                    const headlines = analysisData.data_sources.news_headlines.headlines;
                    if (!Array.isArray(headlines)) return null;
                    
                    return headlines.slice(0, 4).map((headline, index) => (
                      <div key={index} className="headline-item">
                        <div className="headline-text">
                          {headline?.headline || headline}
                        </div>
                        {headline?.url && (
                          <a 
                            href={headline.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="headline-link"
                          >
                            Read More →
                          </a>
                        )}
                      </div>
                    ));
                  } catch (error) {
                    return <div className="error-text">Error loading headlines</div>;
                  }
                })()}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="analysis-dashboard-footer">
          <button className="footer-btn primary" onClick={onClose}>
            <span>←</span>
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnalysisDashboard;