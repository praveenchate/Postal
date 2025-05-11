import React, { useRef, useEffect, useState } from 'react';
import { ArrowLeft, Camera } from 'lucide-react';

interface SingleAddressCaptureProps {
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

const SingleAddressCapture: React.FC<SingleAddressCaptureProps> = ({ onBack }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addressData, setAddressData] = useState<AddressData | null>(null);
  const [loading, setLoading] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);

  useEffect(() => {
    const getCameras = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        setDevices(videoDevices);
        if (videoDevices.length > 0) {
          setSelectedCamera(videoDevices[0].deviceId);
        }
      } catch (err) {
        console.error('Error enumerating devices:', err);
        setError('Could not access camera devices');
      }
    };

    getCameras();
  }, []);

  useEffect(() => {
    const startCamera = async () => {
      if (!selectedCamera) return;

      try {
        // Stop previous stream if exists
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }

        const constraints: MediaStreamConstraints = {
          video: {
            deviceId: { exact: selectedCamera },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        };

        const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
        
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

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [selectedCamera]);

  const handleCameraChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCamera(e.target.value);
  };

  const handleCapture = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!videoRef.current || !stream) {
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

      setAddressData(data);
      setShowResults(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process address';
      setError(errorMessage);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center mb-8">
        <button
          onClick={onBack}
          className="flex items-center text-slate-600 hover:text-slate-900"
          disabled={loading}
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to Dashboard
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Camera Section */}
        <div className="space-y-4">
          {devices.length > 1 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
              <label htmlFor="camera-select" className="block text-sm font-medium text-slate-700 mb-2">
                Select Camera
              </label>
              <select
                id="camera-select"
                value={selectedCamera || ''}
                onChange={handleCameraChange}
                className="block w-full rounded-md border border-slate-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                disabled={loading}
              >
                {devices.map(device => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label || `Camera ${device.deviceId.substring(0, 5)}`}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="relative bg-white rounded-xl shadow-sm border border-slate-200 p-4">
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
              disabled={loading || !!error || !selectedCamera}
              className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 p-4 rounded-full shadow-lg transition-colors ${
                loading || error || !selectedCamera
                  ? 'bg-slate-400 cursor-not-allowed'
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
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
              <h3 className="text-red-800 font-medium mb-2">Error</h3>
              <p className="text-red-600">{error}</p>
            </div>
          ) : showResults && addressData ? (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 divide-y divide-slate-200">
              <div className="p-6">
                <h3 className="text-lg font-medium mb-4">Extracted Address</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-slate-500">Street</label>
                    <p className="font-medium">
                      {addressData.extracted_address.street || 'Not available'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-500">City</label>
                    <p className="font-medium">
                      {addressData.extracted_address.city || 'Not available'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-500">State</label>
                    <p className="font-medium">
                      {addressData.extracted_address.state || 'Not available'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-500">Pincode</label>
                    <p className="font-medium">
                      {addressData.extracted_address.pincode || 'Not available'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <h3 className="text-lg font-medium mb-4">Delivery Center</h3>
                <p className="font-medium">
                  {addressData.nodal_delivery_center || 'Not available'}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Estimated processing time: 2-3 days
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
              <p className="text-slate-500">
                {loading ? 'Processing address...' : 'Capture an address to see the results here'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SingleAddressCapture;