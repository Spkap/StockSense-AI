import React from 'react';
import NewsItem from './NewsItem';

const NewsList = ({ articles, getArticleDate }) => {
  if (!articles || articles.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-white/70">No news articles available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {articles.map((article, index) => (
        <NewsItem 
          key={index} 
          article={article} 
          getArticleDate={getArticleDate} 
        />
      ))}
    </div>
  );
};

export default NewsList;