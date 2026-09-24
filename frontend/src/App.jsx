import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from 'react-leaflet';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { Activity, Map as MapIcon, Plane, TrendingUp, AlertTriangle, CheckCircle2, ServerCrash, Clock } from 'lucide-react';
import L from 'leaflet';

const CITY_COORDS = {
  "DEL": { lat: 28.5562, lon: 77.1000, name: "New Delhi" },
  "BOM": { lat: 19.0896, lon: 72.8656, name: "Mumbai" },
  "BLR": { lat: 13.1986, lon: 77.7066, name: "Bengaluru" },
  "CCU": { lat: 22.6520, lon: 88.4463, name: "Kolkata" },
  "HYD": { lat: 17.2403, lon: 78.4294, name: "Hyderabad" },
  "MAA": { lat: 12.9716, lon: 80.1675, name: "Chennai" },
  "PNQ": { lat: 18.5793, lon: 73.9089, name: "Pune" },
  "AMD": { lat: 23.0734, lon: 72.6346, name: "Ahmedabad" },
  "GOI": { lat: 15.3808, lon: 73.8314, name: "Goa" },
  "COK": { lat: 10.1518, lon: 76.3930, name: "Kochi" }
};

const MOCK_INDEX = [
  { origin: "DEL", destination: "BOM", index_value: 115.2, computed_at_utc: new Date().toISOString() },
  { origin: "BOM", destination: "BLR", index_value: 98.4, computed_at_utc: new Date().toISOString() },
  { origin: "DEL", destination: "BLR", index_value: 106.1, computed_at_utc: new Date().toISOString() },
  { origin: "BLR", destination: "CCU", index_value: 92.5, computed_at_utc: new Date().toISOString() },
  { origin: "DEL", destination: "CCU", index_value: 101.0, computed_at_utc: new Date().toISOString() },
  { origin: "HYD", destination: "MAA", index_value: 108.9, computed_at_utc: new Date().toISOString() },
];

const MOCK_AIRLINES = [
  { name: 'IndiGo', avg_fare: 5400, obs: 45000 },
  { name: 'Air India', avg_fare: 6200, obs: 28000 },
  { name: 'Vistara', avg_fare: 7100, obs: 15000 },
  { name: 'SpiceJet', avg_fare: 4900, obs: 12000 },
  { name: 'Akasa Air', avg_fare: 5100, obs: 8000 },
];

const COLORS = ['#1E3A8A', '#0D9488', '#F59E0B', '#DC2626', '#334155'];

export default function App() {
  const [indexData, setIndexData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    // In production, this would fetch from import.meta.env.VITE_API_URL
    fetch('http://localhost:8000/index/latest')
      .then(res => res.json())
      .then(data => {
        if (data && data.length > 0) {
          setIndexData(data);
        } else {
          setIndexData(MOCK_INDEX);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch from API, using mock data.", err);
        setIndexData(MOCK_INDEX);
        setLoading(false);
        setError(true);
      });
  }, []);

  const getCPIColor = (cpi) => {
    if (cpi > 110) return '#DC2626'; // Red
    if (cpi > 105) return '#F59E0B'; // Orange
    if (cpi < 95) return '#16A34A';  // Green
    return '#1E3A8A';                // Blue
  };

  const getStatusText = (cpi) => {
    if (cpi > 110) return 'Critical';
    if (cpi > 105) return 'Warning';
    if (cpi < 95) return 'Deflation';
    return 'Stable';
  };

  const nationalCPI = indexData.length > 0 
    ? (indexData.reduce((acc, row) => acc + row.index_value, 0) / indexData.length).toFixed(1) 
    : "100.0";

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden text-slate-900 font-sans">
      
      {/* Sidebar */}
      <div className="w-72 bg-gov-navy text-white flex flex-col shadow-2xl relative z-20">
        <div className="p-8 text-center border-b border-white/10">
          <img src="https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg" alt="Gov Logo" className="w-16 mx-auto mb-4 drop-shadow-md brightness-200 contrast-200 grayscale" style={{ filter: 'brightness(0) invert(1)'}} />
          <h2 className="text-xl font-bold tracking-wider mb-1">AirPrice India</h2>
          <p className="text-xs text-white/60 uppercase tracking-widest">National Airfare Monitor</p>
        </div>
        
        <nav className="flex-1 py-6 px-4 space-y-2">
          <a href="#" className="flex items-center space-x-3 px-4 py-3 bg-white/10 rounded-lg text-gov-gold border-l-4 border-gov-gold transition-colors">
            <Activity size={20} />
            <span className="font-semibold">Executive Dashboard</span>
          </a>
          <a href="#" className="flex items-center space-x-3 px-4 py-3 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors border-l-4 border-transparent">
            <MapIcon size={20} />
            <span className="font-medium">Route Surveillance</span>
          </a>
          <a href="#" className="flex items-center space-x-3 px-4 py-3 text-white/70 hover:bg-white/5 hover:text-white rounded-lg transition-colors border-l-4 border-transparent">
            <Plane size={20} />
            <span className="font-medium">Carrier Analytics</span>
          </a>
        </nav>

        <div className="p-6 bg-black/20 border-t border-white/5">
          <div className="text-xs text-white/50 mb-2 font-medium uppercase tracking-wider">System Status</div>
          <div className="flex items-center space-x-2 text-sm">
            {error ? <ServerCrash size={16} className="text-gov-red" /> : <CheckCircle2 size={16} className="text-gov-green" />}
            <span className={error ? "text-gov-red font-medium" : "text-white/90"}>
              {error ? "API Disconnected (Mock)" : "API Connected (Live)"}
            </span>
          </div>
          <div className="flex items-center space-x-2 text-sm mt-3 text-white/70">
            <Clock size={16} />
            <span>Updated: {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        
        {/* Header */}
        <header className="bg-white px-10 py-8 shadow-sm border-b border-slate-200 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center space-x-5">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg" alt="Emblem" className="w-12 drop-shadow-sm" />
            <div>
              <h1 className="text-2xl font-extrabold text-gov-navy leading-tight">National Airfare Monitoring System</h1>
              <p className="text-sm text-slate-500 mt-1 font-medium">Directorate General of Civil Aviation (DGCA) | Ministry of Civil Aviation</p>
            </div>
          </div>
          <div className="bg-gov-gold text-gov-navy px-4 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase shadow-sm">
            SIH26056 - Real-Time Surveillance
          </div>
        </header>

        {/* Dashboard Body */}
        <main className="p-10 max-w-[1600px] w-full mx-auto space-y-8">
          
          {/* KPIs */}
          <div className="grid grid-cols-4 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border-t-4 border-gov-blue hover:-translate-y-1 transition-transform duration-200">
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Total Observations</div>
              <div className="text-3xl font-extrabold text-gov-navy">108,492</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border-t-4 border-gov-blue hover:-translate-y-1 transition-transform duration-200">
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Active Routes</div>
              <div className="text-3xl font-extrabold text-gov-navy">{indexData.length || 0}</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border-t-4 border-gov-gold hover:-translate-y-1 transition-transform duration-200">
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">National CPI</div>
              <div className="text-3xl font-extrabold text-gov-navy flex items-end space-x-2">
                <span>{nationalCPI}</span>
                {parseFloat(nationalCPI) > 100 ? <TrendingUp size={24} className="text-gov-red mb-1" /> : null}
              </div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border-t-4 border-gov-teal hover:-translate-y-1 transition-transform duration-200">
              <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Airlines Tracked</div>
              <div className="text-3xl font-extrabold text-gov-navy">{MOCK_AIRLINES.length}</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-8">
            
            {/* Realistic 2D Map */}
            <div className="col-span-2 bg-white rounded-xl shadow-sm border border-slate-150 overflow-hidden flex flex-col">
              <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                <h3 className="text-lg font-bold text-gov-navy flex items-center gap-2">
                  <MapIcon size={20} className="text-gov-blue" /> CPI Geographical Analysis
                </h3>
                <div className="flex gap-4 text-xs font-semibold">
                  <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-gov-red"></div> Critical (&gt;110)</span>
                  <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-gov-gold"></div> Warning</span>
                  <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-gov-green"></div> Deflation</span>
                  <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-gov-blue"></div> Stable</span>
                </div>
              </div>
              <div className="flex-1 min-h-[500px] relative z-0">
                <MapContainer center={[21.0, 78.5]} zoom={4.5} scrollWheelZoom={true} className="w-full h-full">
                  <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                  />
                  {indexData.map((route, i) => {
                    const orig = CITY_COORDS[route.origin];
                    const dest = CITY_COORDS[route.destination];
                    if (!orig || !dest) return null;
                    const color = getCPIColor(route.index_value);
                    return (
                      <Polyline 
                        key={i} 
                        positions={[[orig.lat, orig.lon], [dest.lat, dest.lon]]} 
                        color={color} 
                        weight={3} 
                        opacity={0.8}
                      >
                        <Tooltip sticky>
                          <div className="font-sans">
                            <strong>{route.origin} → {route.destination}</strong><br/>
                            CPI: <span style={{color}} className="font-bold">{route.index_value.toFixed(1)}</span><br/>
                            Status: {getStatusText(route.index_value)}
                          </div>
                        </Tooltip>
                      </Polyline>
                    );
                  })}
                  {Object.values(CITY_COORDS).map((city, i) => (
                    <CircleMarker 
                      key={`city-${i}`} 
                      center={[city.lat, city.lon]} 
                      radius={4} 
                      pathOptions={{ color: '#0F172A', fillColor: '#FFF', fillOpacity: 1, weight: 2 }}
                    >
                      <Tooltip direction="bottom" offset={[0, 10]} opacity={1} permanent className="bg-transparent border-0 shadow-none text-gov-navy font-bold text-xs p-0 m-0 leading-none">
                        {city.name}
                      </Tooltip>
                    </CircleMarker>
                  ))}
                </MapContainer>
              </div>
            </div>

            {/* CPI Rankings */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-150 flex flex-col">
              <div className="px-6 py-4 border-b border-slate-100">
                <h3 className="text-lg font-bold text-gov-navy flex items-center gap-2">
                  <AlertTriangle size={20} className="text-gov-red" /> Critical Routes
                </h3>
              </div>
              <div className="flex-1 p-6">
                <ResponsiveContainer width="100%" height={450}>
                  <BarChart data={[...indexData].sort((a,b)=> b.index_value - a.index_value).slice(0,10)} layout="vertical" margin={{top: 0, right: 30, left: 20, bottom: 0}}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                    <XAxis type="number" domain={[80, 130]} tick={{fontSize: 12, fill: '#64748B'}} />
                    <YAxis dataKey={(d) => `${d.origin} → ${d.destination}`} type="category" width={80} tick={{fontSize: 12, fill: '#0F172A', fontWeight: 600}} />
                    <RechartsTooltip cursor={{fill: 'transparent'}} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)'}} />
                    <Bar dataKey="index_value" radius={[0, 4, 4, 0]}>
                      {indexData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getCPIColor(entry.index_value)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          <div className="grid grid-cols-2 gap-8">
            {/* Airline Analytics */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-150 flex flex-col">
              <div className="px-6 py-4 border-b border-slate-100">
                <h3 className="text-lg font-bold text-gov-navy">Carrier Average Fares</h3>
              </div>
              <div className="p-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={MOCK_AIRLINES} margin={{top: 20, right: 30, left: 20, bottom: 5}}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="name" tick={{fontSize: 13, fill: '#0F172A', fontWeight: 600}} axisLine={false} tickLine={false} />
                    <YAxis tick={{fontSize: 12, fill: '#64748B'}} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v}`} />
                    <RechartsTooltip cursor={{fill: '#F1F5F9'}} formatter={(value) => [`₹${value.toLocaleString()}`, "Avg Fare"]} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)'}} />
                    <Bar dataKey="avg_fare" fill="#1E3A8A" radius={[4, 4, 0, 0]} maxBarSize={60}>
                      {MOCK_AIRLINES.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-150 flex flex-col">
              <div className="px-6 py-4 border-b border-slate-100">
                <h3 className="text-lg font-bold text-gov-navy">Market Share by Observation Volume</h3>
              </div>
              <div className="p-6 flex items-center justify-center">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={MOCK_AIRLINES}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={120}
                      paddingAngle={2}
                      dataKey="obs"
                      label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      labelLine={false}
                    >
                      {MOCK_AIRLINES.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip formatter={(value) => [value.toLocaleString(), "Observations"]} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)'}} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

        </main>
      </div>
    </div>
  );
}
