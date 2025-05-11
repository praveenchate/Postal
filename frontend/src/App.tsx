import React, { useState } from 'react';
import { Camera, Package, Truck, CheckCircle, Home, History, FileDown, Settings, HelpCircle, Bell } from 'lucide-react';
import BatchAddressCapture from './components/BatchAddressCapture';
import Dashboard from './components/Dashboard';
import SingleAddressCapture from './components/SingleAddressCapture';
import PincodeTable from './components/PincodeTable'; // Add this import

// Add this at the top of App.tsx
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// Extend the View type to include 'pincodes'
type View = 'dashboard' | 'batch' | 'single' | 'pincodes';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 min-h-screen bg-indigo-900 p-6 text-white">
          <div className="mb-8">
            <h2 className="text-2xl font-bold">ParcelPro</h2>
          </div>
          
          <nav className="space-y-2">
            <button 
              onClick={() => setCurrentView('dashboard')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                currentView === 'dashboard' ? 'bg-indigo-700' : 'hover:bg-indigo-800'
              }`}
            >
              <Home size={20} />
              <span>Dashboard</span>
            </button>

            {/* Add Pincodes menu item */}
            <button 
              onClick={() => setCurrentView('pincodes')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                currentView === 'pincodes' ? 'bg-indigo-700' : 'hover:bg-indigo-800'
              }`}
            >
              <Package size={20} />
              <span>Pincodes</span>
            </button>

            <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-indigo-800">
              <History size={20} />
              <span>History</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-indigo-800">
              <FileDown size={20} />
              <span>Export</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-indigo-800">
              <Settings size={20} />
              <span>Settings</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-indigo-800">
              <HelpCircle size={20} />
              <span>Support</span>
            </button>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          {/* Header */}
          <header className="bg-white border-b border-slate-200 px-8 py-4">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">
                  {currentView === 'dashboard' && 'Dashboard'}
                  {currentView === 'batch' && 'Batch Address Capture'}
                  {currentView === 'single' && 'Single Address Capture'}
                  {currentView === 'pincodes' && 'Pincode Database'}
                </h1>
                <p className="text-slate-500">
                  {currentView === 'dashboard' && 'Here\'s what\'s happening with your parcels today.'}
                  {currentView === 'pincodes' && 'Search and manage pincode data'}
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                <button className="p-2 rounded-full hover:bg-slate-100">
                  <Bell size={20} />
                </button>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                    <span className="text-indigo-700 font-medium">AB</span>
                  </div>
                  <span className="font-medium">Praveen Chate</span>
                </div>
              </div>
            </div>
          </header>

          {/* Content */}
          <main className="p-8">
            {currentView === 'dashboard' && (
              <Dashboard 
                onAddSingle={() => setCurrentView('single')} 
                onAddBatch={() => setCurrentView('batch')}
                onViewPincodes={() => setCurrentView('pincodes')} // Add this prop
              />
            )}
            {currentView === 'batch' && <BatchAddressCapture onBack={() => setCurrentView('dashboard')} />}
            {currentView === 'single' && <SingleAddressCapture onBack={() => setCurrentView('dashboard')} />}
            {currentView === 'pincodes' && <PincodeTable />}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;