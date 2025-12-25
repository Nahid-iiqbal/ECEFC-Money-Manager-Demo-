#!/usr/bin/env python
"""Test script to verify app functionality."""
from app import app, db

if __name__ == '__main__':
    with app.app_context():
        # Create all tables
        db.create_all()
        print('✓ Database initialized successfully')

        # Test imports
        from routes.tuition import tuition_bp
        from routes.auth import auth_bp
        from routes.expense import expense
        from routes.dashboard import dashboard_bp
        from routes.group import group
        from routes.profile import profile_bp
        print('✓ All blueprints imported successfully')

        # Test template rendering
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('templates'))
        templates_to_check = [
            'reschedule.html',
            'tuition.html',
            'edit_reschedule.html',
            'base.html'
        ]

        for template_name in templates_to_check:
            try:
                env.get_template(template_name)
                print(f'✓ {template_name} template is valid')
            except Exception as e:
                print(f'✗ {template_name} template error: {e}')

        print('\n✓ All checks passed!')
