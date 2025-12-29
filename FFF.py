import requests

url = "https://redis-service-1.onrender.com/check_connection"

data = {
    "game": "dota2",
    "password": "669ad350340678994430b9605aec8c341171844f64d56a452bc2f806b3355cec10afd1c602e79c717e974b35e44ed7b5e25f847f1bff29f49cf66830136666af"
}

response = requests.post(url, json=data, timeout=10)

print("Status:", response.status_code)
print("Response:", response.text)
