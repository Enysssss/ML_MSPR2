import requests, os

class Authorization():    
    @staticmethod
    def verify_token(token : str) -> bool:
        host = os.environ.get('LARAVEL_HOST')
        if not host.startswith(('http://', 'https://')):
            host = 'http://' + host

        response = requests.get(
            host + ':' + os.environ.get('LARAVEL_PORT') + os.environ.get('LARAVEL_ME_URL'),
            headers = {
                "Authorization": "Bearer " + token
            }
        )
        
        if response.status_code == 200:
            return True
        
        return False