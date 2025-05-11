import React, { useState, useEffect } from "react";

interface Pincode {
  id: number;
  pincode: string;
  office_name: string;
  district: string;
  state_name: string;
  office_type: string;
}

interface ApiResponse {
  data: Pincode[];
  total?: number;
  page?: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const PincodeTable: React.FC = () => {
  const [pincodes, setPincodes] = useState<Pincode[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [searchResults, setSearchResults] = useState<Pincode[]>([]);

  useEffect(() => {
    const fetchPincodes = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/pincodes?page=1&per_page=50`
        );
        const data: ApiResponse = await response.json();
        setPincodes(data.data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching pincodes:", error);
        setLoading(false);
      }
    };

    fetchPincodes();
  }, []);

  const handleSearch = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/pincodes/search?q=${searchTerm}`
      );
      const data: Pincode[] = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error("Error searching pincodes:", error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className="p-4">
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by pincode, office or district..."
          className="p-2 border rounded w-full md:w-1/2"
          value={searchTerm}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button
          onClick={handleSearch}
          className="ml-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Search
        </button>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border">
            <thead>
              <tr className="bg-gray-100">
                <th className="py-2 px-4 border">Pincode</th>
                <th className="py-2 px-4 border">Office Name</th>
                <th className="py-2 px-4 border">District</th>
                <th className="py-2 px-4 border">State</th>
                <th className="py-2 px-4 border">Type</th>
              </tr>
            </thead>
            <tbody>
              {(searchTerm ? searchResults : pincodes).map((pincode) => (
                <tr key={pincode.id} className="hover:bg-gray-50">
                  <td className="py-2 px-4 border">{pincode.pincode}</td>
                  <td className="py-2 px-4 border">{pincode.office_name}</td>
                  <td className="py-2 px-4 border">{pincode.district}</td>
                  <td className="py-2 px-4 border">{pincode.state_name}</td>
                  <td className="py-2 px-4 border">{pincode.office_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PincodeTable;