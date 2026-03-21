import { useState, useEffect } from 'react'

function App() {
  const [dbStatus, setDbStatus] = useState("checking...");
  const [testResult, setTestResult] = useState("");
  const [scrapeResult, setScrapeResult] = useState("");
  const [nlpResult, setNlpResult] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/health')
      .then(res => res.json())
      .then(data => setDbStatus(data.db))
      .catch(err => setDbStatus(`Error fetching API: ${err.message}`));
  }, []);

  const handleTestInsert = () => {
    setTestResult("Inserting...");
    fetch('http://localhost:5000/api/test-db', { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setTestResult(data.message + " Check MongoDB Compass!");
        } else {
          setTestResult("Error: " + data.message);
        }
      })
      .catch(err => setTestResult("Network Error: " + err.message));
  };

  const handleScrapeTest = () => {
    setScrapeResult("Scraping 5 websites... (This may take up to 10 seconds)");
    fetch('http://localhost:5000/api/scrape')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          const firstArticle = data.data.length > 0 ? data.data[0].title : "None";
          setScrapeResult(`Successfully scraped ${data.count} articles! Example: "${firstArticle}"`);
        } else {
          setScrapeResult("Error: " + data.message);
        }
      })
      .catch(err => setScrapeResult("Network Error: " + err.message));
  };

  const handleNlpTest = () => {
    setNlpResult({ status: "loading", msg: "Simulating pipeline... Processing NLP & embeddings..." });
    fetch('http://localhost:5000/api/test-nlp')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setNlpResult({ status: "success", count: data.count, data: data.data });
        } else {
          setNlpResult({ status: "error", msg: "Error: " + data.message });
        }
      })
      .catch(err => setNlpResult({ status: "error", msg: "Network Error: " + err.message }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full text-center">
        <h1 className="text-2xl font-bold text-blue-600 mb-4">Kocaeli Live</h1>
        <div className="text-gray-700 mb-6">
          <p className="mb-2">Frontend: <span className="font-semibold text-green-500">React + Vite OK</span></p>
          <p>Database Status: <span className="font-semibold">{dbStatus}</span></p>
        </div>
        
        <div className="flex flex-col gap-3">
          <button 
            onClick={handleTestInsert}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded transition-colors w-full"
          >
            Phase 1: Insert "Hello World" into MongoDB
          </button>
          
          {testResult && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-800 font-medium">
              {testResult}
            </div>
          )}

          <button 
            onClick={handleScrapeTest}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded transition-colors w-full"
          >
            Phase 2: Test Async Web Scraper
          </button>

          {scrapeResult && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-800 font-medium">
              {scrapeResult}
            </div>
          )}

          <button 
            onClick={handleNlpTest}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded transition-colors w-full"
          >
            Phase 3: Test NLP Classification & Detection
          </button>

          {nlpResult && nlpResult.status === "loading" && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-800 font-medium animate-pulse">
              {nlpResult.msg}
            </div>
          )}

          {nlpResult && nlpResult.status === "success" && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-800 font-medium text-left max-h-48 overflow-y-auto">
              <p className="font-bold mb-2 border-b pb-1">Processed {nlpResult.count} items:</p>
              <ul className="space-y-3">
                {nlpResult.data.map((item, idx) => (
                  <li key={idx} className={`p-2 rounded ${item.is_duplicate ? 'bg-red-100' : 'bg-green-50'}`}>
                    <p className="font-semibold text-xs text-gray-500 mb-1">{item.source} • {item.date.split('T')[0]}</p>
                    <p className="text-gray-900 leading-tight mb-1 truncate">{item.title}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      <span className="bg-purple-200 text-purple-800 px-2 py-0.5 rounded text-xs">Cat: {item.category}</span>
                      <span className="bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded text-xs">Loc: {item.location}</span>
                      {item.is_duplicate && (
                        <span className="bg-red-500 text-white px-2 py-0.5 rounded text-xs font-bold">DUPLICATE REJECTED ({(item.similarity_score*100).toFixed(0)}%)</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {nlpResult && nlpResult.status === "error" && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm font-medium">
              {nlpResult.msg}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App;
