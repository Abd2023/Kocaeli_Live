import React from 'react';
import { ChevronDown, Car, Flame, Zap, ShieldAlert, Music, RefreshCw, Layers } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { tr } from 'date-fns/locale';

const CAT_THEMES = {
  "Tümü": { icon: Layers, bg: "bg-blue-100", text: "text-blue-700", label: "Tümü" },
  "Traffic": { icon: Car, bg: "bg-red-100", text: "text-red-600", label: "Trafik" },
  "Fire": { icon: Flame, bg: "bg-orange-100", text: "text-orange-600", label: "Yangın" },
  "Electricity": { icon: Zap, bg: "bg-yellow-100", text: "text-yellow-600", label: "Elektrik" },
  "Theft": { icon: ShieldAlert, bg: "bg-purple-100", text: "text-purple-600", label: "Hırsızlık" },
  "Culture": { icon: Music, bg: "bg-green-100", text: "text-green-600", label: "Kültür" }
};

const DISTRICTS = [
  "Tüm Kocaeli", "İzmit", "Gebze", "Gölcük", "Karamürsel", 
  "Körfez", "Derince", "Kartepe", "Başiskele", 
  "Çayırova", "Darıca", "Dilovası", "Kandıra"
];

const Sidebar = ({ 
  articles, 
  filteredArticles,
  totalFilteredCount,
  selectedCategory, 
  setSelectedCategory,
  selectedDistrict,
  setSelectedDistrict,
  dateStart,
  setDateStart,
  dateEnd,
  setDateEnd,
  applyFilters,
  handleSync,
  isSyncing,
  onOpenDuplicates,
  showAllNews,
  setShowAllNews,
  setHoveredArticleLink
}) => {
  return (
    <div className="w-[360px] h-full bg-[#FAFAFA] border-r border-gray-200 flex flex-col shrink-0">
      
      {/* Title Section */}
      <div className="p-6 pb-2">
        <h1 className="text-[22px] font-black text-blue-700 tracking-tight leading-tight">Kocaeli Haber Haritası</h1>
        <p className="text-[11px] font-bold text-gray-500 tracking-widest mt-1">CANLI ŞEHİR TAKİBİ</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6 pt-4 block-scrollbar">
        
        {/* Date Range Filter */}
        <div className="mb-5">
          <label className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2 block">Tarih Aralığı</label>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="text-[9px] font-bold text-gray-400 uppercase mb-1 block">Başlangıç</label>
              <input 
                type="date"
                value={dateStart}
                max={dateEnd || undefined}
                onChange={(e) => setDateStart(e.target.value)}
                className="w-full bg-white border border-gray-200 text-gray-700 text-xs font-medium rounded-2xl py-2 px-3 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 appearance-none"
              />
            </div>
            <div className="flex-1">
              <label className="text-[9px] font-bold text-gray-400 uppercase mb-1 block">Bitiş</label>
              <input 
                type="date"
                value={dateEnd}
                min={dateStart || undefined}
                onChange={(e) => setDateEnd(e.target.value)}
                className="w-full bg-white border border-gray-200 text-gray-700 text-xs font-medium rounded-2xl py-2 px-3 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 appearance-none"
              />
            </div>
          </div>
        </div>

        {/* District Filter */}
        <div className="mb-5">
          <label className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2 block">İlçe Seçimi</label>
          <div className="relative">
            <select 
              value={selectedDistrict} 
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="w-full bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-full py-2.5 px-4 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 appearance-none cursor-pointer"
            >
              {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <ChevronDown className="absolute right-4 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* Categories */}
        <div className="mb-6">
          <label className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-3 block">Kategoriler</label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(CAT_THEMES).map(([cat, theme]) => {
              const active = selectedCategory === cat;
              const Icon = theme.icon;
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-bold transition-all border ${
                    active ? `border-transparent ${theme.bg} ${theme.text} shadow-sm ring-1 ring-black/5` : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {theme.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Apply Filters Button */}
        <button 
          onClick={applyFilters}
          className="w-full bg-[#0066FF] hover:bg-blue-600 text-white font-bold text-sm py-3 rounded-full transition-colors shadow-md shadow-blue-500/20 mb-8"
        >
          Filtrele
        </button>

        {/* Son Haberler (Recent News Feed) */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-[10px] font-bold text-gray-500 tracking-widest uppercase">
              Son Haberler {totalFilteredCount > 15 && `(${totalFilteredCount})`}
            </h3>
            {totalFilteredCount > 15 && (
              <span 
                onClick={() => setShowAllNews(!showAllNews)} 
                className="text-[10px] font-bold text-blue-600 uppercase cursor-pointer hover:underline"
              >
                {showAllNews ? "Daha Az Göster" : "Tümünü Gör"}
              </span>
            )}
          </div>
          
          <div className="space-y-3">
            {filteredArticles.map((article, idx) => {
              const theme = CAT_THEMES[article.category] || Object.values(CAT_THEMES)[0];
              const dateObj = article.date ? new Date(article.date) : new Date();
              const timeStr = formatDistanceToNow(dateObj, { addSuffix: true, locale: tr });
              
              return (
                <div 
                  key={idx} 
                  onClick={() => window.open(article.link, "_blank")} 
                  onMouseEnter={() => setHoveredArticleLink(article.link)}
                  onMouseLeave={() => setHoveredArticleLink(null)}
                  className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full ${theme.bg} ${theme.text}`}>
                      {theme.label}
                    </span>
                    <span className="text-[10px] font-semibold text-gray-400">{timeStr}</span>
                  </div>
                  <h4 className="text-[13px] font-bold text-gray-900 leading-snug line-clamp-2">{article.title}</h4>
                  <p className="text-[11px] text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">
                    {article.raw_content}
                  </p>
                </div>
              );
            })}
            
            {filteredArticles.length === 0 && (
              <div className="text-center py-6 text-xs text-gray-400 font-medium">Bu filtrelere uygun haber bulunamadı.</div>
            )}
          </div>
        </div>
      </div>

      {/* Persistent System Action Buttons from PDF Requirements */}
      <div className="p-5 bg-white border-t border-gray-200 shrink-0 space-y-2">
        <button 
          onClick={handleSync}
          disabled={isSyncing}
          className={`w-full py-2.5 rounded-xl font-bold text-sm transition-all flex justify-center items-center gap-2 ${
            isSyncing ? 'bg-blue-50 text-blue-400 cursor-wait' : 'bg-blue-50 hover:bg-blue-100 text-blue-700'
          }`}
        >
          {isSyncing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {isSyncing ? 'Tarama Yapılıyor...' : 'Haberleri Güncelle'}
        </button>
        
        <button 
          onClick={onOpenDuplicates}
          className="w-full py-2.5 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl font-bold text-sm text-gray-600 transition-colors flex justify-center items-center gap-2"
        >
           Tekrar Eden Seçimleri Gör
        </button>
      </div>

    </div>
  );
};

export default Sidebar;
