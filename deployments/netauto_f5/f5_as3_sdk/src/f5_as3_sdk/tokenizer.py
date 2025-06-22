import requests

def get_token(box, creds):
   heads = {"Content-Type":"application/json"}
   token_url = f"https://{box}/mgmt/shared/authn/login"
   token_data = {
      "username":creds[0],
      "password":creds[1],
      "loginProviderName":"tmos"
   }
   req = requests.post(token_url, headers=heads, auth=(creds[0],creds[1]), json=token_data, verify=False)
   return req.json()["token"]["token"]

def prolong_token(box,token):
   heads = {"Content-Type":"application/json", "X-F5-Auth-Token":token}
   data = {"timeout":"36000"}
   prolong_url = f"https://{box}/mgmt/shared/authz/tokens/{token}"
   r = requests.patch(prolong_url, headers=heads, json=data, verify=False)
   return r.json()