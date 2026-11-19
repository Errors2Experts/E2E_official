2# E2E Workshop integration (mounted at /workshop/)

The workshop application is integrated into the official Django project as a separate Django app. Its public home is `/workshop/`; workshop URLs remain under that prefix, e.g. `/workshop/workshops/`, `/workshop/register/`, `/workshop/dashboard/`. The official site's original `/workshops/` page is preserved.

## Local setup
1. Create/activate a virtual environment.
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py collectstatic` (for production)
5. `python manage.py runserver`

## Production notes
- Back up the live database and files before deployment.
- Run `python manage.py migrate` after deploying.
- Ensure the deployment has persistent writable storage for `data/` (registration Excel, private payment screenshots, certificate templates and announcement attachments). The workshop registration workbook is file-based and should be backed up regularly.
- Configure email and Cloudinary environment variables in the deployment. Public workshop posters/gallery images use the project's configured default file storage.
- Ensure static files are collected and served by the deployment.
- This package has not been deployed or end-to-end tested against the live production database. Test in staging first.
