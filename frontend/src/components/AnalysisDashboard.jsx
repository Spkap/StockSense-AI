import React, { useState, useEffect } from 'react';

const AnalysisDashboard = ({ stock, onClose, analysisData }) => {
  const [modalKey, setModalKey] = useState(0);

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

    // Clean up each paragraph and handle markdown formatting
    paragraphs = paragraphs.map(paragraph => {
      // Remove excessive line breaks
      let cleaned = paragraph.replace(/\n{3,}/g, '\n\n').trim();
      // Remove markdown bold formatting
      cleaned = cleaned.replace(/\*\*/g, '');
      return cleaned;
    });

    return paragraphs.join('\n\n');
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
            <div style={{ color: '#ff6b6b', padding: '1rem' }}>
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
              <div key={index} className="headline-analysis-block" style={{
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '1rem'
              }}>
                {section.split('\n').map((line, lineIndex) => {
                  if (line.trim().startsWith('Headline:')) {
                    return (
                      <div key={lineIndex} style={{ 
                        fontWeight: 'bold', 
                        color: '#60a5fa',
                        marginBottom: '0.5rem'
                      }}>
                        📰 {cleanMarkdownText(line.replace('Headline:', ''))}
                      </div>
                    );
                  } else if (line.trim().startsWith('* Sentiment:')) {
                    const sentiment = line.replace('* Sentiment:', '').trim();
                    const sentimentColor = sentiment.toLowerCase().includes('positive') ? '#10b981' :
                                         sentiment.toLowerCase().includes('negative') ? '#ef4444' : '#f59e0b';
                    return (
                      <div key={lineIndex} style={{ 
                        color: sentimentColor, 
                        fontWeight: '600',
                        marginLeft: '1rem',
                        marginBottom: '0.25rem'
                      }}>
                        Sentiment: {sentiment}
                      </div>
                    );
                  } else if (line.trim().startsWith('* Justification:')) {
                    return (
                      <div key={lineIndex} style={{ 
                        color: '#d1d5db',
                        marginLeft: '1rem',
                        fontStyle: 'italic',
                        lineHeight: '1.5'
                      }}>
                        {cleanMarkdownText(line.replace('* Justification:', '').trim())}
                      </div>
                    );
                  } else if (line.trim()) {
                    return (
                      <div key={lineIndex} style={{ color: '#e5e7eb', marginBottom: '0.25rem' }}>
                        {cleanMarkdownText(line)}
                      </div>
                    );
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
                      return (
                        <div key={lineIdx} style={{ 
                          marginBottom: '0.75rem',
                          paddingLeft: '1rem',
                          borderLeft: '3px solid rgba(167, 139, 250, 0.5)'
                        }}>
                          🔹 {cleanMarkdownText(line.replace(/^\*\s*/, ''))}
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
                {items.map((item, itemIndex) => (
                  <div key={itemIndex} className="sentiment-list-item" style={{
                    marginBottom: '0.5rem',
                    color: '#e5e7eb',
                    lineHeight: '1.5'
                  }}>
                    {cleanMarkdownText(item.trim())}
                  </div>
                ))}
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
      <div className="analysis-modal" style={{ 
        maxHeight: '90vh', 
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div className="modal-header" style={{ 
          flex: '0 0 auto',
          minHeight: 'fit-content'
        }}>
          <div className="header-content">
            <div className="company-info">
              <div className="company-icon">
                {analysisData?.analysis?.symbol?.slice(0, 2) || stock?.symbol?.slice(0, 2) || '??'}
              </div>
              <div className="company-details">
                <h2 className="company-name">
                  {analysisData?.analysis?.company_name || stock?.name || analysisData?.analysis?.symbol || 'Unknown Company'}
                </h2>
                <div className="stock-symbol">{analysisData?.analysis?.symbol || stock?.symbol}</div>
              </div>
            </div>
            <button className="close-button" onClick={onClose}>
              <span>×</span>
            </button>
          </div>
        </div>

        <div className="analysis-content" style={{ 
          padding: '1.5rem', 
          gap: '1.5rem', 
          display: 'flex', 
          flexDirection: 'column',
          flex: 1,
          overflow: 'auto',
          minHeight: 0
        }}>
          {/* Investment Verdict */}
          <div className={`verdict-section enhanced ${(analysisData?.analysis?.recommendation || 'unspecified').toLowerCase()}`} 
               style={{ 
                 minHeight: 'fit-content',
                 marginBottom: '1rem',
                 flex: '0 0 auto'
               }}>
            <div className="verdict-header">
              <div className="verdict-icon">
                {analysisData?.analysis?.recommendation === 'BUY' ? '↗' : 
                 analysisData?.analysis?.recommendation === 'SELL' ? '↘' : 
                 analysisData?.analysis?.recommendation === 'HOLD' ? '→' : '?'}
              </div>
              <h4>Investment Verdict</h4>
            </div>
            
            <div className={`verdict-badge enhanced ${(analysisData?.analysis?.recommendation || 'unspecified').toLowerCase()}`}
                 style={{ marginBottom: '1rem' }}>
              {analysisData?.analysis?.recommendation || 'ANALYZING'}
            </div>
            
            <div className="verdict-details" style={{ width: '100%' }}>
              <div className="confidence-meter" style={{ width: '100%' }}>
                <span className="confidence-label">Confidence Level</span>
                <div className="confidence-bar" style={{ margin: '0.5rem 0' }}>
                  <div className={`confidence-fill ${analysisData?.analysis?.confidence || 'medium'}`}
                       style={{width: analysisData?.analysis?.confidence === 'high' ? '90%' : 
                                     analysisData?.analysis?.confidence === 'medium' ? '70%' : '50%'}}>
                  </div>
                </div>
                <span className={`confidence-text ${analysisData?.analysis?.confidence || 'medium'}`}>
                  {(analysisData?.analysis?.confidence || 'MEDIUM').toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Analysis Summary */}
          <div className="summary-section enhanced">
            <div className="section-header">
              <div className="section-icon">🤖</div>
              <h4>AI Analysis Summary</h4>
            </div>
            <div className="summary-content enhanced">
              <div className="summary-text">
                {(() => {
                  try {
                    const formattedSummary = formatSummaryText(analysisData?.analysis?.summary);
                    return (
                      <div className="formatted-summary">
                        {formattedSummary.split('\n\n').map((paragraph, index) => (
                          <p key={index} className="summary-paragraph" 
                             style={{ 
                               marginBottom: '1rem', 
                               lineHeight: '1.7',
                               color: '#e5e7eb',
                               fontSize: '0.95rem'
                             }}>
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    );
                  } catch (error) {
                    console.error('Error rendering summary:', error);
                    return 'Error loading analysis summary';
                  }
                })()}
              </div>
            </div>
          </div>

          {/* Market Sentiment */}
          {analysisData?.analysis?.sentiment_report && (
            <div className="sentiment-section enhanced">
              <div className="section-header">
                <div className="section-icon"></div>
                <h4>Market Sentiment Analysis</h4>
              </div>
              <div className="sentiment-content enhanced">
                {renderSentimentContent(analysisData.analysis.sentiment_report)}
              </div>
            </div>
          )}

          {/* News Analysis */}
          {analysisData?.data_sources?.news_headlines && (
            <div className="news-section enhanced">
              <div className="section-header">
                <div className="section-icon">📰</div>
                <h4>Recent News Analysis</h4>
                <div className="news-count enhanced">
                  {analysisData.data_sources.news_headlines.count || 0} articles
                </div>
              </div>
              <div className="news-grid">
                {(() => {
                  try {
                    const headlines = analysisData.data_sources.news_headlines.headlines;
                    if (!Array.isArray(headlines)) {
                      return <div style={{color: '#ff6b6b'}}>Error: Headlines data is not an array</div>;
                    }
                    return headlines.slice(0, 6).map((headline, index) => (
                      <div key={index} className="news-card enhanced">
                        <div className="news-content">
                          <div className="news-title">{headline?.headline || 'No title available'}</div>
                          {headline?.url && (
                            <a 
                              href={headline.url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="news-link enhanced"
                            >
                              <span>Read article</span>
                              <div className="link-arrow">→</div>
                            </a>
                          )}
                        </div>
                      </div>
                    ));
                  } catch (error) {
                    console.error('Error rendering news:', error);
                    return <div style={{color: '#ff6b6b'}}>Error loading news headlines</div>;
                  }
                })()}
              </div>
            </div>
          )}
        </div>

        <div className="modal-actions" style={{ 
          flex: '0 0 auto',
          minHeight: 'fit-content'
        }}>
          <button className="action-button secondary" onClick={() => window.location.reload()}>
            <span className="button-icon">↻</span>
            <span>New Analysis</span>
          </button>
          <button className="action-button primary" onClick={onClose}>
            <span className="button-icon">←</span>
            <span>Back to Dashboard</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnalysisDashboard;