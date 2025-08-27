# Setting up Celery and Redis for background jobs

This project uses Celery with Redis as a message broker to handle background tasks. Below are the steps to set up and run Celery with Redis.

1. **Install Redis**: Make sure you have Redis installed and running on your machine. You can download it from [redis.io](https://redis.io/download) or use a package manager like `brew` on macOS:

   ```bash
   brew install redis or dockerized redis
   brew services start redis
   ```

2. **Install Celery**: If you haven't already, install Celery and the Redis dependencies in your Django project:

   ```bash
   pip install celery redis
   ```

3. **Configure Celery**: In your Django project settings (e.g., `settings.py`), add the following Celery configuration:

   ```python
   CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
   CELERY_ACCEPT_CONTENT = ['json']
   CELERY_TASK_SERIALIZER = 'json'
   CELERY_RESULT_SERIALIZER = 'json'
   CELERY_TIMEZONE = 'UTC'
   ```

   ```python
   CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },

  }
  ```

4. **Create a Celery app**: In your Django app (e.g., `crm`), create a new file called `celery.py` and add the following code:

   ```python
   from celery import Celery
   import os

   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')

   app = Celery('alx_backend_graphql_crm')
   app.config_from_object('django.conf:settings', namespace='CELERY')
   app.autodiscover_tasks()
   ```

5. **Run Migrations**: Before starting the Celery worker, make sure to run your database migrations:

   ```bash
   python manage.py migrate
   ```

6. **Start Celery worker**: Open a new terminal window and start the Celery worker:

   ```bash
   celery -A crm worker -l info
   ```

7. **Start Celery beat**: If you have periodic tasks, you can start the Celery beat scheduler in another terminal window:

   ```bash
   celery -A crm beat -l info
   ```

8. **Verify logs in**: Check the logs for both the worker and beat processes to ensure that tasks are being processed as expected. You can find the logs in the terminal where you started the processes and at `/tmp/crm_heartbeat_log.txt` and `/tmp/crm_report_log.txt`.

Now your Django project is set up to use Celery with Redis for background tasks. You can create tasks in your Django apps and call them asynchronously using Celery.
