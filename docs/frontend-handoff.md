# Frontend handoff

You own the visual interface. Build pages in `src/iems/templates` and styles/scripts under `src/iems/static`.

During development, use `python run.py --browser`; it makes normal HTML/CSS/JavaScript iteration easy. Flask templates use Jinja syntax, but plain HTML works normally. We will introduce dynamic values only when a screen needs them.

## Suggested screen order

1. Login
2. Main layout: sidebar, top bar, content area
3. Dashboard
4. Income and expense transaction tables/forms
5. Reports
6. User management and audit log (Admin only)

Keep visual work separate from backend calls initially. Once a page looks how you want, we will connect it to a focused Flask endpoint together.
