from locust import HttpUser, task, between


class MyUser(HttpUser):
    wait_time = between(0.1, 1)

    @task
    def scoreboard_task(self):
        self.client.get("/domjudge/public")
