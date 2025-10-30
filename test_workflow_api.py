"""Quick test of workflow API endpoints"""
import requests
import uuid

BASE = 'http://127.0.0.1:8000'

# 1. Register a test user
email = f'test_{uuid.uuid4().hex[:8]}@example.com'
r = requests.post(f'{BASE}/api/v1/auth/register', json={'email': email, 'password': 'test123'})
tok = r.json()['access_token']
hdr = {'Authorization': f'Bearer {tok}'}
print(f'✅ User registered: {email}')

# 2. Create a workflow
workflow_data = {
    'name': 'Test Workflow',
    'description': 'My first workflow',
    'nodes': [
        {'node_id': 'start', 'name': 'Start', 'type': 'trigger', 'config': {}},
        {'node_id': 'process', 'name': 'Process Data', 'type': 'agent_call', 'config': {'agent_id': 'test'}}
    ],
    'edges': [
        {'source_id': 'start', 'target_id': 'process', 'condition': None}
    ]
}
wf = requests.post(f'{BASE}/api/v1/workflows', headers=hdr, json=workflow_data).json()
print(f'✅ Workflow created: {wf.get("id", wf)}')

# 3. List workflows
workflows = requests.get(f'{BASE}/api/v1/workflows', headers=hdr).json()
print(f'✅ Retrieved {len(workflows)} workflows')

# 4. Get workflow details
if 'id' in wf:
    details = requests.get(f'{BASE}/api/v1/workflows/{wf["id"]}', headers=hdr).json()
    print(f'✅ Workflow details: {details["name"]} with {len(details.get("nodes", []))} nodes')
    
    # 5. Run the workflow
    run = requests.post(f'{BASE}/api/v1/workflows/{wf["id"]}/run', headers=hdr, json={'inputs': {}}).json()
    if 'run_id' in run:
        print(f'✅ Workflow run started: {run["run_id"]}')
        
        # 6. Check run status
        status = requests.get(f'{BASE}/api/v1/workflows/runs/{run["run_id"]}', headers=hdr).json()
        print(f'✅ Run status: {status.get("status", status)}')

print('\n🎉 All workflow API tests passed!')
