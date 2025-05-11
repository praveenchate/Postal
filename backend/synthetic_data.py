nodal_centers = {
    "Pune Main Nodal Center": ["411001", "411002", "411003", "411004", "411005"], #Example list.
    "Mumbai Central Nodal Center": ["400001", "400016", "400020", "400021", "400022"], #Example list.
    "Nagpur Regional Nodal Center": ["440001", "440002", "440003", "440004", "440005"], #Example list.
    "Solapur Distribution Hub": ["413001", "413002", "413003", "413004", "413005"], #Example list.
    "Aurangabad Logistics Park": ["431001", "431002", "431003", "431004", "431005"], #Example list.
    "Kolhapur Delivery Center": ["416001", "416002", "416003", "416004", "416005"], #Example list.
    "Thane West Sorting Office": ["400601", "400602", "400603", "400604", "400605"], #Example list.
    "Nashik Main Post Office": ["422001", "422002", "422003", "422004", "422005"], #Example list.
    "Amravati Camp Hub": ["444601", "444602", "444603", "444604", "444605"], #Example list.
    "Akola City Dispatch": ["444001", "444002", "444003", "444004", "444005"], #Example list.
    "Latur City Post Office": ["413512", "413513", "413514", "413515", "413516"], #Example list.
    "Jalgaon City Delivery": ["425001", "425002", "425003", "425004", "425005"], #Example list.
    "Parbhani City Post": ["431401", "431402", "431403", "431404", "431405"], #Example list.
    "New Delhi Central Hub": ["110001", "110002", "110003", "110004", "110006"], #Example list.
    "Bangalore MG Road Center": ["560001", "560002", "560003", "560004", "560005"], #Example list.
    "Kolkata Park Street Hub": ["700001", "700016", "700017", "700018", "700019"], #Example list.
    "Jaipur JLN Marg Center": ["302001", "302002", "302003", "302004", "302005"], #Example list.
    "Ahmedabad MG Road Hub": ["380001", "380002", "380003", "380009", "380010"], #Example list.
    "Hyderabad Sarojini Devi Hub": ["500001", "500002", "500003", "500004", "500005"], #Example list.
    # Add more mappings as needed
}

def get_nodal_center(pincode):
    """Retrieves the nodal delivery center based on the pincode."""
    for center, pincode_list in nodal_centers.items():
        if pincode in pincode_list:
            return center
    return "Nodal Center Not Found"






synthetic_data = [
    {
        "address_text": "123 Ganesh Peth, Pune, Maharashtra 411002",
        "expected_pincode": "411002",
        "expected_city": "Pune",
        "expected_state": "Maharashtra",
        "expected_street": "Ganesh Peth",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "456 Shivaji Nagar, Mumbai, Maharashtra 400016",
        "expected_pincode": "400016",
        "expected_city": "Mumbai",
        "expected_state": "Maharashtra",
        "expected_street": "Shivaji Nagar",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "789 MG Road, Nagpur, Maharashtra 440001",
        "expected_pincode": "440001",
        "expected_city": "Nagpur",
        "expected_state": "Maharashtra",
        "expected_street": "MG Road",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "101 Market Yard, Solapur, Maharashtra 413002",
        "expected_pincode": "413002",
        "expected_city": "Solapur",
        "expected_state": "Maharashtra",
        "expected_street": "Market Yard",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "202 CIDCO, Aurangabad, Maharashtra 431003",
        "expected_pincode": "431003",
        "expected_city": "Aurangabad",
        "expected_state": "Maharashtra",
        "expected_street": "CIDCO",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "303 Juna Bazar, Kolhapur, Maharashtra 416001",
        "expected_pincode": "416001",
        "expected_city": "Kolhapur",
        "expected_state": "Maharashtra",
        "expected_street": "Juna Bazar",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "404 Thane West, Thane, Maharashtra 400601",
        "expected_pincode": "400601",
        "expected_city": "Thane",
        "expected_state": "Maharashtra",
        "expected_street": "Thane West",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "505 Nashik Road, Nashik, Maharashtra 422001",
        "expected_pincode": "422001",
        "expected_city": "Nashik",
        "expected_state": "Maharashtra",
        "expected_street": "Nashik Road",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "606 Amravati Camp, Amravati, Maharashtra 444601",
        "expected_pincode": "444601",
        "expected_city": "Amravati",
        "expected_state": "Maharashtra",
        "expected_street": "Amravati Camp",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "707 Akola City, Akola, Maharashtra 444001",
        "expected_pincode": "444001",
        "expected_city": "Akola",
        "expected_state": "Maharashtra",
        "expected_street": "Akola City",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "808 Latur City, Latur, Maharashtra 413512",
        "expected_pincode": "413512",
        "expected_city": "Latur",
        "expected_state": "Maharashtra",
        "expected_street": "Latur City",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "909 Jalgaon City, Jalgaon, Maharashtra 425001",
        "expected_pincode": "425001",
        "expected_city": "Jalgaon",
        "expected_state": "Maharashtra",
        "expected_street": "Jalgaon City",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "1000 Parbhani City, Parbhani, Maharashtra 431401",
        "expected_pincode": "431401",
        "expected_city": "Parbhani",
        "expected_state": "Maharashtra",
        "expected_street": "Parbhani City",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
        {
        "address_text": "1100 Delhi Gate, New Delhi, Delhi 110006",
        "expected_pincode": "110006",
        "expected_city": "New Delhi",
        "expected_state": "Delhi",
        "expected_street": "Delhi Gate",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "1300 MG Road, Bangalore, Karnataka 560001",
        "expected_pincode": "560001",
        "expected_city": "Bangalore",
        "expected_state": "Karnataka",
        "expected_street": "MG Road",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "1400 Park Street, Kolkata, West Bengal 700016",
        "expected_pincode": "700016",
        "expected_city": "Kolkata",
        "expected_state": "West Bengal",
        "expected_street": "Park Street",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "1500 Jawahar Lal Nehru Marg, Jaipur, Rajasthan 302004",
        "expected_pincode": "302004",
        "expected_city": "Jaipur",
        "expected_state": "Rajasthan",
        "expected_street": "Jawahar Lal Nehru Marg",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "1600 Mahatma Gandhi Road, Ahmedabad, Gujarat 380009",
        "expected_pincode": "380009",
        "expected_city": "Ahmedabad",
        "expected_state": "Gujarat",
        "expected_street": "Mahatma Gandhi Road",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    },
    {
        "address_text": "1700 Sarojini Devi Road, Hyderabad, Telangana 500003",
        "expected_pincode": "500003",
        "expected_city": "Hyderabad",
        "expected_state": "Telangana",
        "expected_street": "Sarojini Devi Road",
        "google_maps_pincode": None,
        "google_maps_city": None,
        "google_maps_state": None,
        "google_maps_street": None,
        "nodal_delivery_center": None
    }
]