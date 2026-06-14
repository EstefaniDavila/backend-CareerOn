from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
response = client.get('/api/recruiter/jobs/3/candidates', headers={'Authorization': 'Bearer mock_token'})
print(response.status_code)
print(response.json())
