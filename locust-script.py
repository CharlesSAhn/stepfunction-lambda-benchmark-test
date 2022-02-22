from locust import HttpUser, task, between
import json
import uuid



class MyUser(HttpUser):
    wait_time = between(1, 3)

    def create_name(self):
        self.name = str(uuid.uuid1())

    @task(1)
    def index(self):

        kb_file = open('data/100kb-test-json.json')
        kb_data = json.load(kb_file)

        headers = {'content-type': 'application/json', 'InvocationType': 'Event'}
        self.client.post('/Prod/validate', json = kb_data, headers=headers)



#locust -f locust-script.py -H ${ApiUrl} --headless -u 250 -r 10 -t 10m
#emulate the access of 250 concurrent users during 10 minutes spawning users at a rate of 10 users/sec


#locust -f locust-script.py -H https://kl6w86p4xk.execute-api.us-east-1.amazonaws.com/Prod/lambda --headless -u 250 -r 50 -t 1m



#locust -f locust-script.py -H https://m826b93rwg.execute-api.us-east-1.amazonaws.com --headless -u 375 -r 50 -t 2m

#locust -f locust-script.py -H https://37jbm2sdl7.execute-api.us-east-1.amazonaws.com --headless -u 250 -r 50 -t 2m