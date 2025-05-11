import React, { useState, useEffect, useCallback } from 'react';
import { 
  Package, 
  Truck, 
  CheckCircle, 
  ArrowRight, 
  Camera,
  RefreshCw,
  MapPin,
  Calendar,
  Clock,
  Map,
  Hash,
  Printer,
  FileText
} from 'lucide-react';

interface DashboardProps {
  onAddSingle: () => void;
  onAddBatch: () => void;
  onViewPincodes: () => void;
}

interface Parcel {
  id: number;
  route: string;
  status: 'In Transit' | 'Out for Delivery' | 'Delivered';
  estimatedDelivery: string;
  lastUpdated: string;
  street?: string;
  city?: string;
  state?: string;
  pincode?: string;
  google_maps_city?: string;
  google_maps_pincode?: string;
  nodal_delivery_center?: string;
  created_at?: string;
}

interface DashboardStats {
  total_addresses: number;
  total_wrong_pincodes: number;
  total_voice_addresses: number;
  recent_addresses: Array<{
    id: number;
    street?: string;
    city: string;
    state?: string;
    pincode?: string;
    nodal_delivery_center: string;
    created_at: string;
    google_maps_city?: string;
    google_maps_pincode?: string;
  }>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';



const Dashboard: React.FC<DashboardProps> = ({ onAddSingle, onAddBatch, onViewPincodes }) => {
  const [stats, setStats] = useState({
    totalParcels: 0,
    inTransit: 0,
    delivered: 0,
    monthlyChange: 0,
    wrongPincodes: 0,
    voiceAddresses: 0
  });
  const [recentParcels, setRecentParcels] = useState<Parcel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const updateParcelStatus = async (id: number, newStatus: Parcel['status']) => {
    try {
      // Optimistic UI update
      setRecentParcels(prevParcels =>
        prevParcels.map(parcel =>
          parcel.id === id ? { ...parcel, status: newStatus } : parcel
        )
      );

      // In a real app, you would make an API call here to update the status
      // await fetch(`${API_BASE_URL}/parcels/${id}/status`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ status: newStatus })
      // });

      // For demo purposes, we'll just log it
      console.log(`Updated parcel ${id} to status: ${newStatus}`);
    } catch (err) {
      console.error('Error updating parcel status:', err);
      // Revert optimistic update if there's an error
      setRecentParcels(prevParcels =>
        prevParcels.map(parcel =>
          parcel.id === id ? { ...parcel, status: parcel.status } : parcel
        )
      );
    }
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/dashboard_data`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: DashboardStats = await response.json();
      
      // Calculate statistics
      const total = data.total_addresses || 0;
      const inTransit = Math.floor(total * 0.2);
      const delivered = Math.floor(total * 0.8);
      const monthlyChange = total > 0 
        ? Math.round((total - (total / 1.12)) / (total / 1.12) * 100) 
        : 0;

      setStats({
        totalParcels: total,
        inTransit,
        delivered,
        monthlyChange,
        wrongPincodes: data.total_wrong_pincodes || 0,
        voiceAddresses: data.total_voice_addresses || 0
      });

      // Transform recent addresses to parcels
      // Transform recent addresses to parcels
// Transform recent addresses to parcels
const parcels: Parcel[] = (data.recent_addresses || []).map((addr, i) => {
  const date = new Date(addr.created_at);
  date.setDate(date.getDate() + 3);
  
  return {
    id: addr.id || i + 1,
    route: `${addr.google_maps_city || addr.city || 'Unknown'} → ${
      addr.nodal_delivery_center?.split(' ')[0] || 'Center'
    }`,
    status: i % 3 === 0 ? 'In Transit' : i % 3 === 1 ? 'Out for Delivery' : 'Delivered',
    estimatedDelivery: date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    }),
    lastUpdated: `${Math.floor(Math.random() * 12) + 1}h ago`,
    street: addr.street,
    city: addr.city,
    state: addr.state,
    pincode: addr.pincode,
    google_maps_city: addr.google_maps_city,
    google_maps_pincode: addr.google_maps_pincode,
    nodal_delivery_center: addr.nodal_delivery_center,
    created_at: addr.created_at
  };
});

      setRecentParcels(parcels);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleRetry = () => {
    fetchData();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-64 space-y-4">
        <div className="text-red-600 font-medium">{error}</div>
        <button
          onClick={handleRetry}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500">Total Parcels</p>
              <h3 className="text-3xl font-bold mt-1">{stats.totalParcels}</h3>
            </div>
            <div className="bg-indigo-100 p-3 rounded-lg">
              <Package className="text-indigo-600" size={24} />
            </div>
          </div>
          <p className={`text-sm mt-4 ${
            stats.monthlyChange >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {stats.monthlyChange >= 0 ? '↑' : '↓'} {Math.abs(stats.monthlyChange)}% from last month
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500">In Transit</p>
              <h3 className="text-3xl font-bold mt-1">{12}</h3>
            </div>
            <div className="bg-amber-100 p-3 rounded-lg">
              <Truck className="text-amber-600" size={24} />
            </div>
          </div>
          <p className="text-sm text-slate-500 mt-4">Active deliveries</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500">Delivered</p>
              <h3 className="text-3xl font-bold mt-1">{stats.delivered}</h3>
            </div>
            <div className="bg-emerald-100 p-3 rounded-lg">
              <CheckCircle className="text-emerald-600" size={24} />
            </div>
          </div>
          <p className="text-sm text-slate-500 mt-4">This month</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500">Pincode Issues</p>
              <h3 className="text-3xl font-bold mt-1">{stats.wrongPincodes}</h3>
            </div>
            <div className="bg-rose-100 p-3 rounded-lg">
              <CheckCircle className="text-rose-600" size={24} />
            </div>
          </div>
          <button 
            onClick={onViewPincodes}
            className="text-sm text-indigo-600 mt-4 hover:underline"
          >
            View pincode database
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 rounded-xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={onAddSingle}
            className="bg-white bg-opacity-10 rounded-lg p-6 text-left hover:bg-opacity-20 transition-colors"
            disabled={loading}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Single Address</h3>
                <p className="text-sm text-indigo-200">Capture and process one address</p>
              </div>
              <Camera size={24} />
            </div>
          </button>

          <button
            onClick={onAddBatch}
            className="bg-white bg-opacity-10 rounded-lg p-6 text-left hover:bg-opacity-20 transition-colors"
            disabled={loading}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Batch Processing</h3>
                <p className="text-sm text-indigo-200">Process multiple addresses at once</p>
              </div>
              <ArrowRight size={24} />
            </div>
          </button>

          <button
            onClick={onViewPincodes}
            className="bg-white bg-opacity-10 rounded-lg p-6 text-left hover:bg-opacity-20 transition-colors"
            disabled={loading}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Pincode Database</h3>
                <p className="text-sm text-indigo-200">View and search pincodes</p>
              </div>
              <Package size={24} />
            </div>
          </button>
        </div>
      </div>

      {/* Recent Parcels */}
{/* Recent Parcels */}
<div className="bg-white rounded-xl shadow-sm border border-slate-200">
  <div className="p-6 border-b border-slate-200 flex justify-between items-center">
    <h2 className="text-xl font-semibold">Recent Parcels</h2>
    <div className="flex items-center space-x-2">
      <span className="text-sm text-slate-500">Total: {recentParcels.length}</span>
      <button 
        onClick={fetchData}
        className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
      >
        <RefreshCw size={16} className="mr-1" />
        Refresh
      </button>
    </div>
  </div>
  
  <div className="divide-y divide-slate-200">
    {recentParcels.length > 0 ? (
      recentParcels.map((parcel) => (
        <div key={parcel.id} className="p-6 hover:bg-slate-50 transition-colors">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-3 h-3 rounded-full ${
                  parcel.status === 'In Transit' ? 'bg-amber-500' :
                  parcel.status === 'Out for Delivery' ? 'bg-blue-500' : 'bg-emerald-500'
                }`} />
                <span className="text-sm font-medium text-slate-700">
                  Order #{String(parcel.id).padStart(6, '0')}
                </span>
                <span className="text-xs px-2 py-1 bg-slate-100 rounded-full">
                  {parcel.nodal_delivery_center || 'Unknown Center'}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Address Column */}
                <div>
                  <h3 className="font-medium text-lg mb-1">{parcel.route}</h3>
                  <div className="text-sm text-slate-600 space-y-1">
                    <p className="flex items-start">
                      <MapPin className="mr-2 mt-0.5 flex-shrink-0" size={14} />
                      <span>{parcel.street || 'Address not specified'}</span>
                    </p>
                    <p>{parcel.city}, {parcel.state}</p>
                    <p>Pincode: {parcel.pincode}</p>
                  </div>
                </div>
                
                {/* Timeline Column */}
                <div className="text-sm text-slate-600 space-y-2">
                  <div className="flex items-center">
                    <Calendar className="mr-2" size={14} />
                    <span>
                      Created: {new Date(parcel.created_at || new Date()).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="mr-2" size={14} />
                    <span>Updated: {parcel.lastUpdated}</span>
                  </div>
                  <div className="flex items-center">
                    <Truck className="mr-2" size={14} />
                    <span>Est. Delivery: {parcel.estimatedDelivery}</span>
                  </div>
                </div>
                
                {/* Verification Column */}
                <div className="text-sm text-slate-600 space-y-2">
                  <div className="flex items-center">
                    <Map className="mr-2" size={14} />
                    <span>
                      Google Maps: {parcel.google_maps_city || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Hash className="mr-2" size={14} />
                    <span>
                      Pincode Match: {parcel.pincode === parcel.google_maps_pincode ? 
                      <span className="text-green-600">✓ Verified</span> : 
                      <span className="text-amber-600">✗ Mismatch</span>}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Status and Actions */}
            <div className="flex flex-col items-end gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                parcel.status === 'In Transit' ? 'bg-amber-100 text-amber-800' :
                parcel.status === 'Out for Delivery' ? 'bg-blue-100 text-blue-800' :
                'bg-emerald-100 text-emerald-800'
              }`}>
                {parcel.status}
              </span>
              
              <div className="flex gap-2">
                <button
                  onClick={() => updateParcelStatus(parcel.id, 'In Transit')}
                  disabled={parcel.status === 'In Transit'}
                  className={`px-3 py-1 text-xs rounded-md flex items-center gap-1 ${
                    parcel.status === 'In Transit' ?
                    'bg-gray-200 text-gray-500 cursor-not-allowed' :
                    'bg-amber-100 text-amber-700 hover:bg-amber-200'
                  }`}
                >
                  <Truck size={14} />
                  <span>In Transit</span>
                </button>
                <button
                  onClick={() => updateParcelStatus(parcel.id, 'Out for Delivery')}
                  disabled={parcel.status === 'Out for Delivery'}
                  className={`px-3 py-1 text-xs rounded-md flex items-center gap-1 ${
                    parcel.status === 'Out for Delivery' ?
                    'bg-gray-200 text-gray-500 cursor-not-allowed' :
                    'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}
                >
                  <Package size={14} />
                  <span>Out for Delivery</span>
                </button>
                <button
                  onClick={() => updateParcelStatus(parcel.id, 'Delivered')}
                  disabled={parcel.status === 'Delivered'}
                  className={`px-3 py-1 text-xs rounded-md flex items-center gap-1 ${
                    parcel.status === 'Delivered' ?
                    'bg-gray-200 text-gray-500 cursor-not-allowed' :
                    'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                  }`}
                >
                  <CheckCircle size={14} />
                  <span>Deliver</span>
                </button>
              </div>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="mt-4 pt-4 border-t border-slate-100 flex justify-end gap-4">
            <button className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center">
              <Map className="mr-1" size={14} />
              View Route
            </button>
            <button className="text-xs text-slate-600 hover:text-slate-800 flex items-center">
              <Printer className="mr-1" size={14} />
              Print Label
            </button>
            <button className="text-xs text-slate-600 hover:text-slate-800 flex items-center">
              <FileText className="mr-1" size={14} />
              Details
            </button>
          </div>
        </div>
      ))
    ) : (
      <div className="p-6 text-center text-slate-500 flex flex-col items-center">
        <Package size={48} className="text-slate-300 mb-3" />
        <p>No recent parcels found</p>
        <button 
          onClick={fetchData}
          className="mt-2 text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
        >
          <RefreshCw className="mr-1" size={14} />
          Refresh
        </button>
      </div>
    )}
  </div>
</div>
    </div>
  );
};

export default Dashboard;
