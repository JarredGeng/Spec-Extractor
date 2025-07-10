import { useState, useEffect } from 'react';

function App() {
  const [url, setUrl] = useState('');
  const [output, setOutput] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewDB, setViewDB] = useState(false);
  const [dbData, setDbData] = useState([]);
  const [search, setSearch] = useState('');

  const API_BASE = 'https://spec-extractor.onrender.com/api';

  const getSpecs = async () => {
    if (!url.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/specs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      setOutput(Object.entries(data));
    } catch (error) {
      setOutput([['Error', error.message]]);
    }
    setLoading(false);
  };

  const fetchDatabase = async () => {
    const res = await fetch(`${API_BASE}/database`);
    const data = await res.json();
    setDbData(data);
  };

  const deleteModel = async (model) => {
    await fetch(`${API_BASE}/delete/${model}`, { method: 'DELETE' });
    fetchDatabase();
  };

  const downloadAll = () => {
    window.open(`${API_BASE}/download-all`, '_blank');
  };

  useEffect(() => {
    if (viewDB) fetchDatabase();
  }, [viewDB]);

  const filteredData = dbData.filter(item =>
    item.Model.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h1>Gigabyte Spec Extractor</h1>

      <button onClick={() => setViewDB(false)} disabled={!viewDB}>
        🔍 Extract Specs
      </button>
      <button onClick={() => setViewDB(true)} disabled={viewDB} style={{ marginLeft: 10 }}>
        📁 View Database
      </button>

      {!viewDB && (
        <div>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste URL here..."
            style={{ width: '60%', padding: 10, marginTop: 20 }}
          />
          <button onClick={getSpecs} style={{ marginLeft: 10, padding: '10px 20px' }}>
            Get Specs
          </button>

          {loading && <p>🔄 Fetching specs...</p>}

          <table style={{ marginTop: 20, borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr>
                <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left' }}>Specification</th>
                <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {output.map(([key, value], i) => (
                <tr key={i}>
                  <td style={{ padding: '6px 10px' }}>{key}</td>
                  <td style={{ padding: '6px 10px' }}>{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {viewDB && (
        <div style={{ marginTop: 20 }}>
          <input
            type="text"
            placeholder="Search model..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ padding: 8, width: '40%' }}
          />
          <button onClick={downloadAll} style={{ marginLeft: 10, padding: '6px 12px' }}>⬇️ Download All</button>

          <table style={{ marginTop: 20, borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>#</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>Model</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>Date</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((item, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td>{item.Model}</td>
                  <td>{item['Date Scraped'] || '-'}</td>
                  <td>
                    <a href={`${API_BASE}/download/${item.Model}`} target="_blank" rel="noopener noreferrer">📄 Download XLSX</a>
                    <button onClick={() => deleteModel(item.Model)} style={{ marginLeft: 10, color: 'red' }}>
                      ❌ Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;
