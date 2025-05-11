import React, { useRef, useEffect, useState } from 'react';
import { ArrowLeft, Camera, CheckCircle } from 'lucide-react';

interface BatchAddressCaptureProps {
  onBack: () => void;
}

interface AddressData {
  extracted_address: {
    street: string;
    city: string;
    state: string;
    pincode: string;
  };
  nodal_delivery_center: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const BatchAddressCapture: React.FC<BatchAddressCaptureProps> = ({ onBack }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [capturedAddresses, setCapturedAddresses] = useState<number>(0);
  const [addresses, setAddresses] = useState<AddressData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    // Start camera stream
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            width: { ideal: 1280 },
            height: { ideal: 720 }
          } 
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          setStream(mediaStream);
        }
      } catch (err) {
        setError('Could not access camera. Please check permissions.');
        console.error('Error accessing camera:', err);
      }
    };

    startCamera();

    // Cleanup function to stop the stream when component unmounts
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const handleCapture = async () => {
    try {
      if (capturedAddresses >= 3) return;
      
      setLoading(true);
      setError(null);
      
      if (!videoRef.current) {
        throw new Error('Video stream not available');
      }

      // Capture image from video
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        throw new Error('Could not create canvas context');
      }

      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      const imageData = canvas.toDataURL('image/jpeg', 0.8); // 80% quality

      // Send to Flask backend
      const response = await fetch(`${API_BASE_URL}/capture_and_process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imageData }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to process address');
      }

      setAddresses(prev => [...prev, data]);
      setCapturedAddresses(prev => Math.min(prev + 1, 3));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process address';
      setError(errorMessage);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetCapture = () => {
    setAddresses([]);
    setCapturedAddresses(0);
    setError(null);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={onBack}
          className="flex items-center text-slate-600 hover:text-slate-900"
          disabled={loading}
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to Dashboard
        </button>
        {capturedAddresses > 0 && (
          <button
            onClick={resetCapture}
            className="flex items-center text-red-600 hover:text-red-800"
            disabled={loading}
          >
            Reset Capture
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Camera Section */}
        <div className="relative">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            {error ? (
              <div className="w-full aspect-[4/3] bg-slate-100 rounded-lg flex items-center justify-center">
                <p className="text-slate-500">{error}</p>
              </div>
            ) : (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full rounded-lg bg-slate-100"
                style={{ aspectRatio: '4/3' }}
              />
            )}
            <button
              onClick={handleCapture}
              disabled={loading || capturedAddresses >= 3 || !!error}
              className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 p-4 rounded-full shadow-lg transition-colors ${
                loading || capturedAddresses >= 3 || error
                  ? 'bg-slate-300 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
              }`}
            >
              {loading ? (
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
              ) : (
                <Camera size={24} />
              )}
            </button>
          </div>
          <p className="text-center mt-4 text-slate-500">
            {capturedAddresses}/3 addresses captured
          </p>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
              <h3 className="text-red-800 font-medium mb-2">Error</h3>
              <p className="text-red-600">{error}</p>
              <button
                onClick={resetCapture}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200">
              <div className="p-6 border-b border-slate-200">
                <h3 className="text-lg font-medium">Captured Addresses</h3>
              </div>
              
              <div className="divide-y divide-slate-200">
                {[1, 2, 3].map(i => (
                  <div key={i} className="p-6 flex items-center">
                    <div className="mr-4">
                      {addresses[i-1] ? (
                        <CheckCircle className="text-emerald-500" size={24} />
                      ) : (
                        <div className="w-6 h-6 rounded-full border-2 border-slate-300" />
                      )}
                    </div>
                    <div className="flex-1">
                      {addresses[i-1] ? (
                        <>
                          <p className="font-medium">
                            {addresses[i-1].extracted_address.street || 'Street not available'}
                          </p>
                          <p className="text-sm text-slate-500">
                            {addresses[i-1].extracted_address.city || 'City not available'}, 
                            {addresses[i-1].extracted_address.state || 'State not available'} 
                            {addresses[i-1].extracted_address.pincode || 'Pincode not available'}
                          </p>
                        </>
                      ) : (
                        <p className="text-slate-400">Address {i} not yet captured</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {capturedAddresses === 3 && (
                <div className="p-6 bg-emerald-50 border-t border-emerald-100">
                  <div className="flex items-center text-emerald-700">
                    <CheckCircle size={20} className="mr-2" />
                    <p className="font-medium">All addresses captured successfully!</p>
                  </div>
                  <div className="mt-4">
                    <p className="text-sm text-emerald-600">
                      Delivery centers: {addresses.map(a => a.nodal_delivery_center).join(', ')}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BatchAddressCapture;