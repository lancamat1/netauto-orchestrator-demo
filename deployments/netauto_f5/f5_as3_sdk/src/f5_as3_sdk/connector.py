import f5_as3_sdk.tokenizer as tokenizer, requests, warnings, json, copy
from f5_as3_sdk.errors import F5Error, EvilError, NoContentError

class AS3Applications:
    warnings.filterwarnings("ignore")

    # Constructor
    def __init__(self, box, user, password):
        self.box = box
        self.url = "https://"+box
        self.token = tokenizer.get_token(box, (user,password))
        #tokenizer.prolong_token(self.box, self.token)
        self.headers = {"Content-Type":"application/json", "X-F5-Auth-Token":self.token}

    # ------------------------------------------------------------------------------------------------------
    # HTTP method functions

    def __get (self, uri):
        r = requests.get(self.url+uri, headers=self.headers, verify=False)
        if r.status_code != 200:
            raise F5Error(r.json())
        return r.json()
        
    def __post (self, uri, data):
        r = requests.post(self.url+uri, headers=self.headers, verify=False, json=data)
        if r.status_code != 200:
            raise F5Error(r.json())
        try:
            return_data = r.json()
        except ValueError:
            return_data = None
        return return_data
    
    def __delete(self, uri):
        r = requests.delete(self.url+uri, headers=self.headers, verify=False)
        if r.status_code == 404:
            print(f"Object {uri} not found, nothing to delete!")
            return None
        if r.status_code != 200:
            raise F5Error(r.json())
        try:
            return_data = r.json()
        except ValueError:
            return_data = None
        return return_data
    
    # ------------------------------------------------------------------------------------------------------
    # HELPER INTERNAL FUNCTIONS
    
    def __tmsh(self, command):
        payload = {"command": "run", "utilCmdArgs":f" -c '{command}'"}
        r = self.__post("/mgmt/tm/util/bash", payload)
        return r
    
    def __create_csr(self, cert_data):
        r = self.__post("/mgmt/tm/sys/crypto/key", cert_data)
        self.__tmsh(f"rm -f /config/ssl/ssl.csr/{cert_data['name']}")
        return r
   
    def __get_csr(self, csr):
        r = self.__tmsh(f"tmsh list sys crypto csr {csr}")
        csr_text = r.get("commandResult").split("\nsys crypto")[0]
        return csr_text
    
    def __upload_file(self, filename):
        with open(filename, "rb") as rf:
            up_file = rf.read()
        size = len(up_file)
        if size == 0:
            raise NoContentError("No content to upload in file...")
        range = f"0-{size-1}/{size}"
      
        headers = copy.deepcopy(self.headers)
        headers.update({"Content-type" : "application/octet-stream", "Content-Range": range})
        r = requests.post(f"{self.url}/mgmt/shared/file-transfer/uploads/{filename}", headers=headers, verify=False, data=up_file)
        if r.status_code == 200:
            return f"/var/config/rest/downloads/{filename}"
        else:
            raise F5Error(r.json())
        

    def ensure_per_app(self):
        # TODO Maybe also check that AS3 is in version 3.50 + ??
        sets = self.__get ("/mgmt/shared/appsvcs/settings")
        if not sets["perAppDeploymentAllowed"]:
            self.__post("/mgmt/shared/appsvcs/settings", { "perAppDeploymentAllowed": True })


    # ------------------------------------------------------------------------------------------------------
    # PUBLIC FUNCTIONS

    def post_app(self, tenant, data):
        r = self.__post(f"/mgmt/shared/appsvcs/declare/{tenant}/applications", data)
        return r
    
    def get_app(self, tenant, app_name):
        r = self.__get(f"/mgmt/shared/appsvcs/declare/{tenant}/applications/{app_name}")
        return r
    
    def delete_app(self, tenant, app_name):
        r = self.__delete(f"/mgmt/shared/appsvcs/declare/{tenant}/applications/{app_name}")
        return r
    
    def save_app(self, tenant, app_name):
        app = self.get_app(tenant, app_name)
        with open(f"{app_name}_saved.json", "w") as wf:
            json.dump(app, wf, indent=4)


    # ------------------------------------------------------------------------------------------------------
    # CERTIFICATE MANIPULATION

    def get_custom_csr(self, cert_data):
        csr_req = self.__create_csr(cert_data)
        csr_text = self.__get_csr(csr_req["name"])
        return csr_text

    def push_certificate(self, crt_file, cert_name):
        tmp_file = self.__upload_file(crt_file)
        data = {"name": cert_name, "fromLocalFile": tmp_file, "command": "install"}
        try:
            r = self.__post("/mgmt/tm/sys/crypto/cert", data)
        finally:
            try:
                self.__tmsh(f"rm -f {tmp_file}")
            except F5Error as e:
                raise EvilError("Temporary file deletion failed") from e
        print(r)

    def get_custom_certificate(self, ca_data):
        # create CSR
        # get CSR from F5
        csr = self.get_custom_csr(ca_data["csr_data"])
        print(csr)
        # send CSR to CA
        # get certificate from CA
        self.create_cert(ca_data["certificate"])
        # upload cert to F5

    def delete_custom_certificate(self, cert):
        # delete cert, key and csr object in F5
        self.__delete(f"/mgmt/tm/sys/crypto/cert/{cert}.crt")
        self.__delete(f"/mgmt/tm/sys/crypto/key/{cert}.key")
        self.__delete(f"/mgmt/tm/sys/crypto/csr/{cert}.key")



    # CREATE DUMMY CERT
    def create_cert(self, cert_name):
        self.__tmsh(f"openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /config/ssl/ssl.key/{cert_name}.key -out /config/ssl/ssl.crt/{cert_name}.crt -subj /CN={cert_name}/L=Seattle/ST=Washington")
        cert = {"command":"install","name":f"{cert_name}.crt","from-local-file":f"/config/ssl/ssl.crt/{cert_name}.crt"}
        key = {"command":"install","name":f"{cert_name}.key","from-local-file":f"/config/ssl/ssl.key/{cert_name}.key"}
        self.__post("/mgmt/tm/sys/crypto/cert", cert)
        self.__post("/mgmt/tm/sys/crypto/key", key)
        self.__tmsh(f"rm -f /config/ssl/ssl.crt/{cert_name}.crt")
        self.__tmsh(f"rm -f /config/ssl/ssl.key/{cert_name}.key")