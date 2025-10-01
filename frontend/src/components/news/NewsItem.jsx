import React from 'react';

const NewsItem = ({ article, getArticleDate }) => {
  const truncateDescription = (text, maxLength = 150) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="bg-black border border-white rounded-lg overflow-hidden">
      <div className="flex">
        <div className="flex-1 p-4">
          <h1 className="font-semibold text-sm mb-2 line-clamp-2 text-white text-xl">
            {article.title}
          </h1>
          <p className="text-md text-white/70 mb-3">
            {truncateDescription(article.description)}
          </p>
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-2">
              <span className="text-md text-white/60">
                {article.source}
              </span>
              <span className="text-xs text-white/50">•</span>
              <span className="text-xs text-white/60">
                {getArticleDate(article)}
              </span>
            </div>
          </div>
          
          <div className="flex justify-between items-center pt-3 border-t border-white/20">
            <a 
              href={article.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
            >
              Read More
            </a>
            
            <div className="flex items-center gap-2 text-xs text-white/60">
              {article.sentiment && (
                <span className={`px-2 py-1 text-xs rounded ${
                  article.sentiment === 'positive' ? 'bg-green-600 text-white' : 
                  article.sentiment === 'negative' ? 'bg-red-600 text-white' : 
                  'bg-gray-600 text-white'
                }`}>
                  {article.sentiment}
                </span>
              )}
            </div>
          </div>
        </div>
        
        {article.image_url && (
          <div className="w-32 flex-shrink-0">
            <img 
              src={article.image_url} 
              alt={article.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsItem;