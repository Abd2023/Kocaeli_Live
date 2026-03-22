import React from 'react';
import { X, ExternalLink, ShieldAlert } from 'lucide-react';

const DuplicateReportModal = ({ isOpen, onClose, articles }) => {
  if (!isOpen) return null;

  // Filter only articles that actually matched with semantic duplicates
  const duplicateEvents = articles.filter(a => a.duplicate_links && a.duplicate_links.length > 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="bg-slate-800 p-6 flex justify-between items-center border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-500/20 rounded-xl">
              <ShieldAlert className="w-8 h-8 text-red-500" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white tracking-tight">AI Tekrar Eden Haber Raporu</h2>
              <p className="text-slate-400 text-sm mt-1">
                TF-IDF Semantik Benzerlik motoru tarafından %90+ benzerlik oranı ile tespit edilip birleştirilen haberler.
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-full text-slate-300 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {duplicateEvents.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-slate-400 text-lg">Şu anda veritabanında tekrar eden (duplicate) haber tespit edilmedi.</p>
            </div>
          ) : (
            duplicateEvents.map((event, idx) => (
              <div key={idx} className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 shadow-lg">
                
                {/* Original Article */}
                <div className="mb-4">
                  <span className="bg-green-500/20 text-green-400 text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">
                    Orijinal Haber ({event.source})
                  </span>
                  <h3 className="text-lg font-bold text-white mt-2 leading-snug">{event.title}</h3>
                  <p className="text-slate-400 text-sm mt-1 mb-2 line-clamp-2">{event.raw_content}</p>
                  <a href={event.link} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 text-sm font-semibold flex items-center gap-1">
                    Orijinal Habere Git <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                {/* The Duplicates */}
                <div className="pl-6 border-l-2 border-slate-700 space-y-4">
                  {event.duplicate_links.map((dup, d_idx) => (
                    <div key={d_idx} className="bg-slate-800 border border-red-500/30 rounded-lg p-4">
                      <span className="bg-red-500/20 text-red-400 text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">
                        Yapay Zeka Tarafından Birleştirildi ({dup.source})
                      </span>
                      <h4 className="text-md font-semibold text-slate-200 mt-2 leading-snug">{dup.title}</h4>
                      <a href={dup.link} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 text-sm font-semibold flex items-center gap-1 mt-2">
                        Kopya Habere Git <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  ))}
                </div>

              </div>
            ))
          )}
        </div>

      </div>
    </div>
  );
};

export default DuplicateReportModal;
