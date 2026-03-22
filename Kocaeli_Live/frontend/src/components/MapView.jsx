import React, { useState } from 'react';
import { APIProvider, Map, AdvancedMarker, InfoWindow } from '@vis.gl/react-google-maps';
import { Car, Flame, Zap, ShieldAlert, Music, ExternalLink, Layers } from 'lucide-react';

const CAT_THEMES = {
  "Tümü": { icon: Layers, bg: "bg-blue-600" },
  "Traffic": { icon: Car, bg: "bg-red-500", label: "Trafik" },
  "Fire": { icon: Flame, bg: "bg-orange-500", label: "Yangın" },
  "Electricity": { icon: Zap, bg: "bg-yellow-500", label: "Elektrik" },
  "Theft": { icon: ShieldAlert, bg: "bg-purple-500", label: "Hırsızlık" },
  "Culture": { icon: Music, bg: "bg-green-500", label: "Kültür" }
};

// Deterministic Pseudo-Random Generator (Fixes the dancing pins bug!)
const getPseudoRandom = (str) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = Math.imul(31, hash) + str.charCodeAt(i) | 0;
  return (Math.abs(hash) % 100) / 100;
};

const MapView = ({ articles, hoveredArticleLink }) => {
  const [selectedArticle, setSelectedArticle] = useState(null);

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  return (
    <APIProvider apiKey={apiKey}>
      <div className="w-full h-full relative">
        <Map
          defaultCenter={{ lat: 40.7654, lng: 29.9408 }} // Kocaeli coordinates
          defaultZoom={11}
          mapId={'DEMO_MAP_ID'}
          disableDefaultUI={true}
          className="w-full h-full"
        >
          {articles.map((article, index) => {
            if (!article.lat || !article.lng) return null;
            
            const theme = CAT_THEMES[article.category] || CAT_THEMES["Tümü"];
            const Icon = theme.icon;

            // Deterministic Jitter implementation so pins physically isolate themselves constantly without randomly dancing!
            const jitterLat = article.lat + (getPseudoRandom(article.link + "lat") - 0.5) * 0.02;
            const jitterLng = article.lng + (getPseudoRandom(article.link + "lng") - 0.5) * 0.02;
            
            const isHovered = hoveredArticleLink === article.link;

            return (
              <AdvancedMarker
                key={index}
                position={{ lat: jitterLat, lng: jitterLng }}
                onClick={() => setSelectedArticle(article)}
                zIndex={isHovered ? 1000 : 1}
              >
                {/* Custom SVG Figma Pin! */}
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white border-[2.5px] border-white shadow-xl cursor-pointer transition-all duration-300 ${theme.bg} ${isHovered ? 'scale-[1.4] ring-4 ring-blue-500 shadow-2xl' : 'hover:scale-110'}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </AdvancedMarker>
            );
          })}

          {selectedArticle && (
            <InfoWindow
              position={{ 
                lat: selectedArticle.lat + (getPseudoRandom(selectedArticle.link + "lat") - 0.5) * 0.02, 
                lng: selectedArticle.lng + (getPseudoRandom(selectedArticle.link + "lng") - 0.5) * 0.02
              }}
              onCloseClick={() => setSelectedArticle(null)}
              pixelOffset={[0, -20]}
            >
              <div className="p-3 w-64 font-sans bg-white text-gray-900 rounded-xl shadow-sm">
                <div className="flex justify-between items-center mb-1.5">
                  <span className={`text-[10px] font-black uppercase tracking-wider ${CAT_THEMES[selectedArticle.category]?.bg.replace('bg-', 'text-') || 'text-blue-600'}`}>
                    {CAT_THEMES[selectedArticle.category]?.label || selectedArticle.category}
                  </span>
                  <span className="text-[10px] text-gray-400 font-semibold font-mono">
                    {selectedArticle.date ? new Date(selectedArticle.date).toLocaleDateString('tr-TR') : ''}
                  </span>
                </div>
                
                <h3 className="font-bold text-sm leading-snug mb-2">
                  {selectedArticle.title}
                </h3>
                
                <p className="text-[11px] text-gray-500 font-medium mb-3">
                  Kaynak: {selectedArticle.sources.map(s => s.toUpperCase()).join(", ")}
                </p>

                <a 
                  href={selectedArticle.link} 
                  target="_blank" 
                  rel="noreferrer"
                  className="w-full py-2 bg-[#0066FF] hover:bg-blue-600 font-bold text-white text-xs text-center rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm shadow-blue-500/30"
                >
                  Habere Git <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </InfoWindow>
          )}
        </Map>
      </div>
    </APIProvider>
  );
};

export default MapView;
