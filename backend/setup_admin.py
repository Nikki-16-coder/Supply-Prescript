"""
SupplyPrescript - Safe Initial Administrator Setup CLI
Provides safe initial-admin configuration using environment variables,
CLI arguments, or secure interactive terminal prompts.

Usage:
  python backend/setup_admin.py
  python backend/setup_admin.py --username admin --email admin@corp.com --role admin
  ADMIN_USERNAME=admin ADMIN_PASSWORD=StrongPassword123! python backend/setup_admin.py
"""

import os
import sys
import getpass
import argparse

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    init_db,
    create_user,
    get_user_by_username_or_email,
    get_connection,
    hash_password,
)


def setup_admin():
    parser = argparse.ArgumentParser(
        description="SupplyPrescript - Safe Administrator Provisioning Tool"
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("ADMIN_USERNAME", "admin"),
        help="Administrator username (default: 'admin' or $ADMIN_USERNAME)",
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("ADMIN_EMAIL", "admin@supplyprescript.corp"),
        help="Administrator email (default: 'admin@supplyprescript.corp' or $ADMIN_EMAIL)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("ADMIN_PASSWORD", None),
        help="Administrator password (or env $ADMIN_PASSWORD). If omitted, prompts securely.",
    )
    parser.add_argument(
        "--role",
        default=os.environ.get("ADMIN_ROLE", "admin"),
        choices=["admin", "manager", "analyst"],
        help="Assigned role (default: 'admin')",
    )
    parser.add_argument(
        "--full-name",
        default=os.environ.get("ADMIN_FULL_NAME", "Executive Administrator"),
        help="Display full name",
    )

    args = parser.parse_args()

    init_db()

    username = args.username.strip()
    email = args.email.strip()
    role = args.role.strip()
    full_name = args.full_name.strip()
    password = args.password

    # Prompt securely if password was not provided via arguments or environment variables
    if not password:
        if sys.stdin.isatty():
            print(f"Provisioning administrator account for: {username} <{email}>")
            password = getpass.getpass("Enter administrator password: ")
            confirm = getpass.getpass("Confirm administrator password: ")
            if password != confirm:
                print("Error: Passwords do not match. Aborting.")
                sys.exit(1)
        else:
            print("Error: No password provided via --password or $ADMIN_PASSWORD.")
            sys.exit(1)

    if len(password) < 6:
        print("Error: Password must be at least 6 characters.")
        sys.exit(1)

    existing_user = get_user_by_username_or_email(username)
    if existing_user:
        # Update existing account's password and role
        pwd_hash, salt = hash_password(password)
        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE users
                SET email = ?, password_hash = ?, salt = ?, role = ?, full_name = ?, is_active = 1
                WHERE id = ?
                """,
                (email, pwd_hash, salt, role, full_name, existing_user["id"]),
            )
            conn.commit()
            print(f"Successfully updated administrator account '{username}' (ID: {existing_user['id']}) with role '{role}'.")
        finally:
            conn.close()
    else:
        # Create brand-new administrator account
        try:
            user_id = create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                full_name=full_name,
            )
            print(f"Successfully provisioned administrator account '{username}' (ID: {user_id}) with role '{role}'.")
        except Exception as exc:
            print(f"Error provisioning user: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    setup_admin()
