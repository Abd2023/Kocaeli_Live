import React, { useState, useEffect } from 'react';
import { Bell, User } from 'lucide-react';
import Sidebar from './components/Sidebar';
import MapView from './components/MapView';
import DuplicateReportModal from './components/DuplicateReportModal';

function App() {
  const [articles, setArticles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDuplicateModalOpen, setIsDuplicateModalOpen] = useState(false);
  
  // Interaction States
  const [showAllNews, setShowAllNews] = useState(false);
  const [hoveredArticleLink, setHoveredArticleLink] = useState(null);
  
  // Pending Sidebar States (Wait for Apply/Filtrele button)
  const [tempCategory, setTempCategory] = useState("Tümü");
  const [tempDistrict, setTempDistrict] = useState("Tüm Kocaeli");
  const [tempDate, setTempDate] = useState("");

  // Active Applied Filters (Drives the Map and Feed)
  const [activeCategory, setActiveCategory] = useState("Tümü");
  const [activeDistrict, setActiveDistrict] = useState("Tüm Kocaeli");
  const [activeDate, setActiveDate] = useState("");

  // Fetch all saved articles
  const fetchNews = () => {
    fetch('http://localhost:5000/api/news', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setArticles(data.data);
        }
        setIsLoading(false);
      })
      .catch(err => {
        console.error(err);
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchNews();
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch("http://localhost:5000/api/sync-news", { method: 'POST' });
      const data = await res.json();
      console.log("Scrape/NLP Status:", data);
      fetchNews(); // Refresh the map seamlessly
    } catch (err) {
      console.error("Sync Error:", err);
    }
    setIsSyncing(false);
  };

  const applyFilters = () => {
    setActiveCategory(tempCategory);
    setActiveDistrict(tempDistrict);
    setActiveDate(tempDate);
  };

  // Compute Filtered View dynamically based on active filters
  const filteredArticles = articles.filter(article => {
    const matchCategory = activeCategory === "Tümü" || article.category === activeCategory;
    
    // Some basic normalisation for District
    const formattedCat = article.location ? article.location.trim().toLowerCase() : "";
    const formattedSel = activeDistrict.trim().toLowerCase();
    const matchDistrict = activeDistrict === "Tüm Kocaeli" || formattedCat.includes(formattedSel) || formattedSel.includes(formattedCat);
    
    // Basic date parsing filtering
    let matchDate = true;
    if (activeDate && article.date) {
      const artDate = new Date(article.date).toISOString().split('T')[0];
      matchDate = artDate === activeDate;
    }

    return matchCategory && matchDistrict && matchDate;
  });

  const visibleArticles = showAllNews ? filteredArticles : filteredArticles.slice(0, 15);

  return (
    <div className="h-screen w-full flex flex-col font-sans bg-gray-50 overflow-hidden">
      
      {/* Top Navigation Bar - Figma Design */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 z-20 shadow-sm">
        <a href="/" className="text-xl font-bold text-[#0066FF] tracking-tight hover:opacity-80 transition-opacity">Kocaeli Live</a>
        <div className="flex items-center gap-7">
          <button className="text-[#0066FF] text-sm font-bold border-b-2 border-[#0066FF] pb-5 pt-5 px-1">Harita</button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 h-[calc(100vh-64px)] relative">
        <Sidebar 
          articles={articles}
          filteredArticles={visibleArticles}
          totalFilteredCount={filteredArticles.length}
          selectedCategory={tempCategory}
          setSelectedCategory={setTempCategory}
          selectedDistrict={tempDistrict}
          setSelectedDistrict={setTempDistrict}
          dateRange={tempDate}
          setDateRange={setTempDate}
          applyFilters={applyFilters}
          handleSync={handleSync}
          isSyncing={isSyncing}
          onOpenDuplicates={() => setIsDuplicateModalOpen(true)}
          showAllNews={showAllNews}
          setShowAllNews={setShowAllNews}
          setHoveredArticleLink={setHoveredArticleLink}
        />
        
        <div className="flex-1 relative bg-gray-100">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-100/50 backdrop-blur-sm z-50">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}
          <MapView articles={visibleArticles} hoveredArticleLink={hoveredArticleLink} />
        </div>
      </div>

      <DuplicateReportModal 
        isOpen={isDuplicateModalOpen} 
        onClose={() => setIsDuplicateModalOpen(false)} 
        articles={articles} 
      />
    </div>
  );
}

export default App;
