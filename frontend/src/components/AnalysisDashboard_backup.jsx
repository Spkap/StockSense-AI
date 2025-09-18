import React, { useState, useEffect } from 'react';
import PriceChart from './PriceChart';
import './AnalysisDashboard.css';

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

    // Clean up each paragraph
    paragraphs = paragraphs.map(paragraph => {
      // Remove excessive line breaks
      return paragraph.replace(/\n{3,}/g, '\n\n').trim();
    });

    return paragraphs.join('\n\n');
  };

  const renderSentimentContent = (content) => {
  if (!content) return null;
  
  // Ensure content is a string
  if (typeof content !== 'string') {
    // Try to convert object to string if it's an object
    if (typeof content === 'object') {
      try {
        content = JSON.stringify(content, null, 2);
      } catch (e) {
        return (
          <div style={{ color: '#ff6b6b', padding: '1rem' }}>
            <p>Error: Unable to display sentiment content - invalid data type</p>
          </div>
        );
      }
    } else {
      // Convert other types to string
      content = String(content || '');
    }
  }

  // Split content into sections and format accordingly
  const sections = content.split('\n\n');
  
  return sections.map((section, index) => {
    // Handle main headers (with **)
    if (section.startsWith('**') && section.includes(':**')) {
      const headerText = section.replace(/\*\*/g, '').replace(':', '');
      return (
        <div key={index} className="sentiment-header">
          <h5>{headerText}</h5>
        </div>
      );
    }
    
    // Handle numbered list items (headlines analysis)
    if (/^\d+\./.test(section.trim())) {
      const lines = section.split('\n');
      const headline = lines[0].replace(/^\d+\.\s*/, '').replace(/\*\*/g, '');
      const details = lines.slice(1).join('\n');
      
      return (
        <div key={index} className="headline-analysis-item">
          <div className="headline-text">{headline}</div>
          {details && (
            <div className="headline-details">
              {details.split('\n').map((line, lineIndex) => {
                if (line.trim().startsWith('*')) {
                  const cleanLine = line.replace(/^\s*\*\s*/, '').replace(/\*\*/g, '');
                  const [label, ...rest] = cleanLine.split(':');
                  if (rest.length > 0) {
                    return (
                      <div key={lineIndex} className="detail-line">
                        <span className="detail-label">{label}:</span>
                        <span className="detail-value">{rest.join(':').trim()}</span>
                      </div>
                    );
                  }
                }
                return null;
              })}
            </div>
          )}
        </div>
      );
    }
    
    // Handle bullet points
    if (section.includes('* **')) {
      const bullets = section.split('\n').filter(line => line.trim().startsWith('*'));
      return (
        <div key={index} className="bullet-section">
          {bullets.map((bullet, bulletIndex) => {
            const cleanBullet = bullet.replace(/^\s*\*\s*/, '').replace(/\*\*/g, '');
            const [term, ...description] = cleanBullet.split(':');
            return (
              <div key={bulletIndex} className="bullet-item">
                <span className="bullet-term">{term}:</span>
                <span className="bullet-description">{description.join(':').trim()}</span>
              </div>
            );
          })}
        </div>
      );
    }
    
    // Handle regular paragraphs
    if (section.trim()) {
      const cleanSection = section.replace(/\*\*/g, '');
      return (
        <div key={index} className="sentiment-paragraph">
          {cleanSection}
        </div>
      );
    }
    
    return null;
  }).filter(Boolean);

  // Now use formatSummaryText in the component
  return (
    <div className="modal-overlay">
      <div className="analysis-modal enhanced">
        <div className="modal-header enhanced">
          <div className="header-content">
            <div className="company-info">
              <div className="company-icon enhanced">
                {analysisData?.analysis?.symbol?.slice(0, 2) || stock?.symbol?.slice(0, 2) || '??'}
              </div>
              <div className="company-details">
                <h2 className="company-name">
                  {analysisData?.analysis?.company_name || stock?.name || analysisData?.analysis?.symbol || 'Unknown Company'}
                </h2>
                <div className="stock-symbol enhanced">{analysisData?.analysis?.symbol || stock?.symbol}</div>
              </div>
            </div>
            <button className="close-button enhanced" onClick={onClose}>
              <span>×</span>
            </button>
          </div>
        </div>

        <div className="modal-content enhanced">
          {/* Enhanced Investment Verdict */}
          <div className="verdict-section enhanced">
            <div className="verdict-header">
              <div className="verdict-icon">
                {analysisData?.analysis?.recommendation === 'BUY' ? '↗' : 
                 analysisData?.analysis?.recommendation === 'SELL' ? '↘' : 
                 analysisData?.analysis?.recommendation === 'HOLD' ? '→' : '?'}
              </div>
              <h4>Investment Verdict</h4>
            </div>
            
            <div className={`verdict-badge enhanced ${(analysisData?.analysis?.recommendation || 'unspecified').toLowerCase()}`}>
              {analysisData?.analysis?.recommendation || 'ANALYZING'}
            </div>
            
            <div className="verdict-details">
              <div className="confidence-meter">
                <span className="confidence-label">Confidence Level</span>
                <div className="confidence-bar">
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

          {/* Enhanced Analysis Summary */}
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
                      <div style={{ whiteSpace: 'pre-line', lineHeight: '1.6' }}>
                        {formattedSummary}
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

          {/* Enhanced Market Sentiment */}
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

          {/* Enhanced News Analysis */}
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
              <div className="source-attribution enhanced">
                <div className="source-icon">🔗</div>
                <span>Source: {analysisData.data_sources.news_headlines.source || 'Multiple Sources'}</span>
              </div>
            </div>
          )}

          {/* Price Chart Section */}
          {analysisData?.chart_data && (
            <div className="price-chart-section">
              <div className="chart-header">
                <h3 className="chart-title">Price Analysis</h3>
                <div className="chart-period-badge">
                  30 Days
                </div>
              </div>
              <PriceChart data={analysisData.chart_data} symbol={stock?.symbol} />
            </div>
          )}
        </div>

        <div className="modal-actions enhanced">
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
  const [loadingStep, setLoadingStep] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);
  
  const loadingSteps = [
    { icon: '', text: 'Initializing AI analysis', description: 'Preparing the ReAct agent' },
    { icon: '', text: 'Collecting market data', description: 'Fetching price history and technical indicators' },
    { icon: '', text: 'Gathering news sentiment', description: 'Analyzing recent market news and headlines' },
    { icon: '', text: 'AI processing', description: 'Running sentiment analysis and pattern recognition' },
    { icon: '', text: 'Generating insights', description: 'Synthesizing data into actionable recommendations' },
    { icon: '', text: 'Finalizing report', description: 'Preparing comprehensive analysis results' }
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
                    <span className="step-description">{step.description}</span>
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
                {loadingSteps[loadingStep]?.description || 'Processing comprehensive market analysis'}
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

  if (!analysisData) {
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
  
  return (
    <div className="modal-overlay" style={{ zIndex: 9999 }}>
      <div className="modal-content analysis-modal results-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header results-header">
          <div className="header-content">
            <div className="stock-info">
              <div className="stock-symbol-large">{stock?.symbol}</div>
              <h3 style={{ color: '#ffffff' }}>AI Analysis Results</h3>
              <div className="analysis-timestamp">
                Analyzed on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
              </div>
            </div>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
        </div>

        <div className="analysis-content" style={{ color: '#ffffff' }}>
          {/* Debug Section */}
          <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.1)', margin: '1rem', borderRadius: '8px' }}>
            <h4 style={{ color: '#ffffff' }}>Debug Information:</h4>
            <p style={{ color: '#ffffff' }}>Analysis Data Keys: {analysisData ? Object.keys(analysisData).join(', ') : 'None'}</p>
            <p style={{ color: '#ffffff' }}>Stock Symbol: {stock?.symbol || 'N/A'}</p>
            <p style={{ color: '#ffffff' }}>Recommendation: {analysisData?.analysis?.recommendation || 'N/A'}</p>
          </div>

          {/* Investment Verdict Section - Enhanced */}
          <div className={`verdict-section enhanced ${(analysisData?.analysis?.recommendation || 'unspecified').toLowerCase()}`}>
            <div className="verdict-header">
              <div className="verdict-icon">
                {analysisData?.analysis?.recommendation === 'BUY' ? '↗' : 
                 analysisData?.analysis?.recommendation === 'SELL' ? '↘' : 
                 analysisData?.analysis?.recommendation === 'HOLD' ? '→' : '?'}
              </div>
              <h4>Investment Verdict</h4>
            </div>
            
            <div className={`verdict-badge enhanced ${(analysisData?.analysis?.recommendation || 'unspecified').toLowerCase()}`}>
              {analysisData?.analysis?.recommendation || 'ANALYZING'}
            </div>
            
            <div className="verdict-details">
              <div className="confidence-meter">
                <span className="confidence-label">Confidence Level</span>
                <div className="confidence-bar">
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

          {/* Enhanced Analysis Summary */}
          <div className="summary-section enhanced">
            <div className="section-header">
              <div className="section-icon">🤖</div>
              <h4>AI Analysis Summary</h4>
            </div>
            <div className="summary-content enhanced">
              <div className="summary-text">
                {(() => {
                  try {
                    return analysisData?.analysis?.summary || 'No analysis summary available';
                  } catch (error) {
                    console.error('Error rendering summary:', error);
                    return 'Error loading analysis summary';
                  }
                })()}
              </div>
            </div>
          </div>

          {/* Enhanced Market Sentiment */}
          {analysisData?.analysis?.sentiment_report && (
            <div className="sentiment-section enhanced">
              <div className="section-header">
                <div className="section-icon"></div>
                <h4>Market Sentiment Analysis</h4>
              </div>
              <div className="sentiment-content enhanced">
                {(() => {
                  try {
                    return renderSentimentContent(analysisData.analysis.sentiment_report);
                  } catch (error) {
                    console.error('Error rendering sentiment content:', error);
                    return (
                      <div style={{ color: '#ff6b6b', padding: '1rem', background: 'rgba(255,107,107,0.1)', borderRadius: '8px' }}>
                        <p>Error displaying sentiment analysis</p>
                        <p>Raw data: {JSON.stringify(analysisData.analysis.sentiment_report, null, 2)}</p>
                      </div>
                    );
                  }
                })()}
              </div>
            </div>
          )}

          {/* Enhanced Recent News Headlines */}
          {analysisData?.data_sources?.news_headlines?.headlines && (
            <div className="news-section enhanced">
              <div className="section-header">
                <div className="section-icon">📰</div>
                <h4>Recent Market News</h4>
                <div className="news-count-badge">
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
              <div className="source-attribution enhanced">
                <div className="source-icon">🔗</div>
                <span>Source: {analysisData.data_sources.news_headlines.source || 'Multiple Sources'}</span>
              </div>
            </div>
          )}

          {/* Price Chart Section */}
          {analysisData?.chart_data && (
            <div className="price-chart-section">
              <div className="chart-header">
                <h3 className="chart-title">Price Analysis</h3>
                <div className="chart-period-badge">
                  30 Days
                </div>
              </div>
              {/* <PriceChart data={analysisData.chart_data} symbol={stock?.symbol} /> */}
              <div style={{ padding: '2rem', textAlign: 'center', color: '#ffffff' }}>
                Price Chart Component (Temporarily Disabled)
              </div>
            </div>
          )}
        </div>

        <div className="modal-actions enhanced">
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
