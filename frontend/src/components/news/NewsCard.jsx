import React, { useState, useEffect } from 'react';
import { newsAPI } from '../../services/api/newsAPI';
import NewsList from './NewsList';
import { RefreshCcw } from 'lucide-react';


const NewsCard = () => {
  const [newsData, setNewsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWatchlistNews();
  }, []);

  const fetchWatchlistNews = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await newsAPI.getWatchlistNews(5);
      
      if (result.success) {
        setNewsData(result);
      } else {
        setError(result.error || 'Failed to fetch news');
      }
    } catch (err) {
      setError(err.message || 'An error occurred while fetching news');
      console.error('Error fetching watchlist news:', err);
    } finally {
      setLoading(false);
    }
  };

  const getArticleDate = (article) => {
    const possibleDateFields = [
      'published_at',  
      'published_on',
      'publishedAt', 
      'date',
      'pubDate',
      'created_at',
      'createdAt'
    ];
    
    for (const field of possibleDateFields) {
      if (article[field]) {
        return formatDate(article[field]);
      }
    }
    
    console.warn('No valid date field found in article:', Object.keys(article));
    return 'Date not available';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    
    try {
      // Handle different date formats
      let date;
      
      // If it's already a Date object
      if (dateString instanceof Date) {
        date = dateString;
      }
      // If it's a timestamp (number)
      else if (typeof dateString === 'number') {
        date = new Date(dateString * 1000); // Convert from Unix timestamp if needed
      }
      // If it's a string (like ISO 8601: "2025-10-01T03:30:00.000000Z")
      else {
        // Handle ISO format or other string formats
        date = new Date(dateString);
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid date:', dateString);
        return 'Invalid date';
      }
      
      // Format the date to be more readable
      const now = new Date();
      const diffInHours = Math.abs(now - date) / (1000 * 60 * 60);
      
      // If less than 24 hours ago, show relative time
      if (diffInHours < 24) {
        const diffInMinutes = Math.floor(diffInHours * 60);
        if (diffInMinutes < 60) {
          return `${diffInMinutes}m ago`;
        } else {
          return `${Math.floor(diffInHours)}h ago`;
        }
      }
      // If less than 7 days, show days ago
      else if (diffInHours < 168) {
        const days = Math.floor(diffInHours / 24);
        return `${days}d ago`;
      }
      // Otherwise show formatted date
      else {
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
      }
    } catch (error) {
      console.error('Error formatting date:', error, dateString);
      return 'Date unavailable';
    }
  };

  if (loading) {
    return (
      <div className="bg-black border border-white rounded-lg p-6">
        <h2 className="text-white text-xl font-bold mb-4">News</h2>
        <div className="flex flex-col items-center justify-center py-8">
          <span className="loading loading-spinner loading-lg text-white"></span>
          <p className="mt-4 text-white/70">Loading latest news...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-black border border-white rounded-lg p-6">
        <h2 className="text-white text-xl font-bold mb-4">News</h2>
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
          <span className="text-red-400">{error}</span>
          <button 
            className="btn btn-sm btn-outline text-white border-white hover:bg-white hover:text-black ml-4" 
            onClick={fetchWatchlistNews}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!newsData || newsData.articles.length === 0) {
    return (
      <div className="bg-black border border-white rounded-lg p-6">
        <h2 className="text-white text-xl font-bold mb-4">News</h2>
        <div className="text-center py-8">
          <p className="text-white/70">No news available for your watchlist stocks</p>
          {newsData?.symbols.length === 0 && (
            <p className="text-sm text-white/50 mt-2">
              Add some stocks to your watchlist to see related news
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-black border border-white rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-white text-xl font-bold">News</h2>
        <div className="flex items-center gap-2">
         
          <button 
            className="btn btn-ghost btn-sm text-white hover:bg-white/10" 
            onClick={fetchWatchlistNews}
            title="Refresh news"
          >
            <RefreshCcw />
          </button>
        </div>
      </div>


      <NewsList articles={newsData.articles} getArticleDate={getArticleDate} />
    </div>
  );
};

export default NewsCard;