# quiz-master-app-v2
Project for Modern App development II course in the diploma level of IITM BSc online course.

Instructions to Run
You will need to open a separate terminal for each of the following services.

1)Run the Redis Server - Starts the message broker required for background tasks and caching.
`sudo service redis-server start`

2)Run the Flask Backend - Starts the main API server.
Navigate to the Backend folder.
`python app.py`

3)Run the Celery Worker - Starts the worker process that executes background jobs like sending emails and exporting files.
Navigate to the Backend folder.
`python run_worker.py`

4)Run the Celery Beat Scheduler - Starts the scheduler that triggers periodic tasks like daily reminders and monthly reports.
`python run_beat.py`

5)Run the Vue.js Frontend - Starts the user interface.

The instructions to start the frontend development server are located in the README.md file inside the Frontend folder.


Milestone 0 completed with git tracker.

Milestone 2 completed with JWT based login and RBAC decorators enabled.

Milestone 1 completed with database schema creation.

Milestone 3 completed with admin dashboard creation and subject,chapter and quiz modification.

Milestone 6 completed with quiz scheduling.

Milestone 4 completed with user dashboard implementation

Milestone 7 completed with celery based backend jobs

Milestone 5 completed with quiz history and result summaries

Milestone 8 completed with search functionalities

Milestone 9 completed with csv export for users.

Milestone 10 completed with redis caching and optimization

Additional milestone 12 completed with analysis and leaderboard features.

 Milestone 13-Final Submission bug fixes and error log updated