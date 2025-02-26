from setuptools import setup, find_packages

setup(
    name="gdrive_uploader",
    version="0.2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-api-python-client>=2.107.0",
        "google-auth-httplib2>=0.1.1",
        "google-auth-oauthlib>=1.1.0",
        "tqdm>=4.66.1",
        "pandas>=2.2.0",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "gdrive-uploader=gdrive_uploader:main",
        ],
    },
    author="User",
    author_email="user@example.com",
    description="A tool to upload folders from local machine to Google Drive",
    keywords="google, drive, upload, folder",
    python_requires=">=3.6",
)
