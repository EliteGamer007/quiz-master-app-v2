# Project Error & Troubleshooting Log

This document logs the major errors encountered and resolved during the development of the Quiz Master application.

## Backend Errors

### 1. JWT Data validation error

- **Error Message**: `POST /api/admin/subjects HTTP/1.1" 422 -` with a response body indicating "subject must be a string". This was the most challenging error to fix and took more than a week.

- **Cause**: This error was caused by the frontend sending an incorrect data type in the JSON payload when creating or editing a subject. For example, a `null` or numeric value was sent for the subject's `title` instead of a string. This was also inherently coming from the way JWT tokens were being sent.

- **Solution**: The frontend data handling in the `AdminDashboard.vue` component was fixed to ensure that the `title` and `description` fields are always sent as strings. This issue took a significant amount of time to debug due to the error also appearing unexpectedly on `GET` requests under certain conditions, which initially masked the true cause.

### 2. Circular Import Errors

- **Error Message**: `ImportError: cannot import name 'user_required' from partially initialized module 'routes.auth_routes' (most likely due to a circular import)`

- **Cause**: This error occurred multiple times when different route files (`user_routes.py`, `admin_routes.py`) tried to import decorators from `auth_routes.py`. This created a dependency loop that Python could not resolve.

- **Solution**: The final, stable solution was to create two new files:
    1.  `extensions.py`: To instantiate all shared Flask extension objects (`db`, `cache`, `limiter`, `mail`).
    2.  `decorators.py`: To define the shared `@user_required` and `@admin_required` decorators.
    
    All other files were updated to import these shared components from their new, central locations, which completely breaks the circular dependencies.

### 3. Celery & Eventlet Integration Errors (Windows)

- **Error Message**: `socket.gaierror: [Errno 11002] Lookup timed out` and `AttributeError: module 'eventlet.patcher' has no attribute 'unpatch'`

- **Cause**: These errors were caused by a conflict between `eventlet`'s patched networking and the blocking I/O operation of sending an email, which requires a DNS lookup.

- **Solution**: The `send_email` function in `tasks.py` was updated to wrap the blocking `mail.send(msg)` call in `eventlet.tpool.execute()`. This delegates the operation to a native OS thread, preventing it from interfering with `eventlet`'s main event loop.

### 4. Database & Configuration Errors

- **Error Message**: `RuntimeError: The current Flask app is not registered with this 'SQLAlchemy' instance.`

- **Cause**: This occurred when the `models.py` file was creating its own `SQLAlchemy()` instance instead of importing the shared instance from `extensions.py`.

- **Solution**: The `models.py` file was updated to import the `db` object from `extensions.py`, ensuring the entire application uses a single, correctly initialized database instance.

- **Error Message**: `AttributeError: 'str' object has no attribute '__dict__'`

- **Cause**: A typo in `app.py` where a configuration value was passed as a string (`'sqlalchemy.pool.NullPool'`) instead of the required class object (`NullPool`).

- **Solution**: The `NullPool` class was imported from `sqlalchemy.pool` and passed directly in the configuration.


### 5. Celery Email Sending
- **Error Message**: `RuntimeError: Working outside of application context.`

- **Cause**: This was a persistent and challenging error that occurred when running Celery with `eventlet` on Windows. It happens when parts of the Flask application (especially extensions like Flask-JWT-Extended) are accessed before the application context is available, often during the complex startup and monkey-patching process of the worker.

- **Status**:  The final, stable solution required a significant restructuring of the Celery startup process to delay the creation of the Flask application until after the worker process has been fully initialized. This was achieved by using a separate `celeryconfig.py` file, the `@worker_process_init` Celery signal, and dedicated `run_worker.py`/`run_beat.py` startup scripts.

## Frontend Errors

### 1. Compilation Errors

- **Error Message**: `Module not found: Error: Can't resolve 'chart.js/auto'`

- **Cause**: The components were trying to `import` the Chart.js library, but it was only included via a CDN link and had not been installed as a local npm package.

- **Solution**: The Chart.js library was installed via npm (`npm install chart.js`), and the redundant CDN script tag was removed from `public/index.html`.

- **Error Message**: `'result' is assigned a value but never used (no-unused-vars)`

- **Cause**: A declared variable in the `AdminDashboard.vue` script was assigned a value from an API call but was never used, causing the linter to raise an error.

- **Solution**: The unused variable declaration was removed.

### 2. Runtime Errors

- **Error Message**: `TypeError: _ctx.toggleSubject is not a function`

- **Cause**: The template was trying to call a method that was missing from the component's script, usually due to the file being out of sync with recent code changes.

- **Solution**: The component's script was updated with the correct and complete set of methods.


