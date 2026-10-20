#!/usr/bin/env python3
"""One-time local OAuth consent for the AD&C private MCP Worker.
Requires: python -m pip install google-auth-oauthlib
Run from user's computer with downloaded Google Cloud 'Desktop app' client_secrets.json.
Never commit refresh token or client_secrets.json.
"""
import argparse
from pathlib import Path

SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/drive.readonly',
]


def main():
    parser = argparse.ArgumentParser(description='AD&C YouTube OAuth bootstrap; do not commit tokens')
    parser.add_argument('--credentials', default='client_secrets.json', help='OAuth Desktop app JSON downloaded from Google Cloud Console')
    args = parser.parse_args()
    p = Path(args.credentials)
    if not p.is_file():
        parser.error('OAuth Desktop app JSON file not found: ' + str(p))
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(str(p), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True, prompt='consent', access_type='offline')
    if not creds.refresh_token:
        raise SystemExit('No refresh token returned. Check OAuth configuration and consent.')
    print('\n=== GOOGLE_REFRESH_TOKEN (SECRET) ===\n')
    print(creds.refresh_token)
    print('\nRegister this directly as a Cloudflare Worker secret. Never put it into GitHub/Drive/AD&C shared KB.\n')
    print('Also set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from the desktop OAuth JSON as Worker secrets.')


if __name__ == '__main__':
    main()
